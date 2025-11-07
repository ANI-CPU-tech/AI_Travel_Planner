# assistant/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db import transaction
from .models import Conversation, Message
from .serializers import ChatRequestSerializer, ConversationSerializer
from .services import generate_safe_reply
from Location.serializers import LocationSerializer, HomesSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db.models import Q
from .services import generate_safe_reply
from Location.models import Location, Homes
# No scrapers: we prefer to persist Gemini-generated values into models
import requests
from django.core.files.base import ContentFile
from django.utils.text import slugify

class ChatView(APIView):
    permission_classes = [permissions.AllowAny] 

    @transaction.atomic
    def post(self, request):
        ser = ChatRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        conv_id = ser.validated_data.get("conversation_id")
        user_msg = ser.validated_data["message"]
        model_name = ser.validated_data.get("model_name") or "gemini-2.5-flash"

        if request.user.is_authenticated:
            user = request.user
            session_id = None
        else:
            user = None
            session_id = request.session.session_key or request.session.create() or request.session.session_key

        if conv_id:
            conversation = Conversation.objects.select_for_update().get(id=conv_id)
        else:
            conversation = Conversation.objects.create(
                user=user, session_id=session_id, model_name=model_name
            )

        Message.objects.create(conversation=conversation, role="user", content=user_msg)

        history = [{"role": m.role, "content": m.content} for m in conversation.messages.order_by("created_at")]
        reply_text = generate_safe_reply(history, model_name=conversation.model_name)

        Message.objects.create(conversation=conversation, role="assistant", content=reply_text)
        # Additionally, attempt to persist any Gemini-generated primary_destination
        # into the database immediately when the user submits a prompt. This uses
        # the same mapping logic as the classification endpoint but runs inline
        # so records exist after the chat turn.
        try:
            gemini_data = generate_safe_reply(user_msg)
            classification = gemini_data.get("fallback") if isinstance(gemini_data, dict) and gemini_data.get("fallback") else gemini_data
            pd = classification.get("primary_destination") if isinstance(classification, dict) else None
            if pd and pd.get("location"):
                name = pd.get("location").strip()
                desc = pd.get("description") or ""
                city = pd.get("city") or pd.get("location_city") or pd.get("region") or name
                country = pd.get("country") or pd.get("location_country")
                best_time = pd.get("best_time_to_visit") or pd.get("best_time")
                avg_cost = None
                try:
                    c = pd.get("average_cost") or pd.get("avg_cost") or pd.get("price")
                    if c is not None:
                        avg_cost = float(str(c).replace("$", "").replace(",", ""))
                except Exception:
                    avg_cost = None

                rating = None
                try:
                    r = pd.get("rating")
                    if r is not None:
                        rating = float(r)
                except Exception:
                    rating = None

                category = pd.get("category") or pd.get("type") or "city"
                image_url = None
                if isinstance(pd.get("image"), str) and pd.get("image"):
                    image_url = pd.get("image")
                else:
                    image_url = f"https://source.unsplash.com/featured/?{name.replace(' ', '+')}"

                lower_msg = (user_msg or "").lower()
                desc_text = (desc or "").lower()
                hotel_keywords = ["hotel", "stay", "accommodation", "booking", "book", "inn", "resort", "hostel", "bnb", "room", "suite"]
                looks_like_hotel = any(k in lower_msg for k in hotel_keywords) or any(k in desc_text for k in hotel_keywords)

                if looks_like_hotel:
                    obj = Homes.objects.filter(location_name__iexact=name).first()
                    if not obj:
                        obj = Homes.objects.create(
                            location_name=name,
                            city=city,
                            country=country,
                            description=desc,
                            category=category if category in dict(Homes.CATEGORY_CHOICES) else "city",
                            best_time_to_visit=best_time,
                            average_cost=avg_cost,
                            rating=rating,
                        )
                        try:
                            headers = {"User-Agent": "Mozilla/5.0"}
                            resp = requests.get(image_url, headers=headers, timeout=10)
                            if resp.status_code == 200 and resp.content:
                                filename = f"{slugify(name)[:50]}.jpg"
                                obj.location_image.save(filename, ContentFile(resp.content), save=True)
                        except Exception:
                            pass
                else:
                    obj = Location.objects.filter(location_name__iexact=name).first()
                    if not obj:
                        obj = Location.objects.create(
                            location_name=name,
                            city=city,
                            country=country,
                            description=desc,
                            category=category if category in dict(Location.CATEGORY_CHOICES) else "city",
                            best_time_to_visit=best_time,
                            average_cost=avg_cost,
                            rating=rating,
                        )
                        try:
                            headers = {"User-Agent": "Mozilla/5.0"}
                            resp = requests.get(image_url, headers=headers, timeout=10)
                            if resp.status_code == 200 and resp.content:
                                filename = f"{slugify(name)[:50]}.jpg"
                                obj.location_image.save(filename, ContentFile(resp.content), save=True)
                        except Exception:
                            pass
        except Exception:
            # Non-fatal: keep chat flow working even if persistence fails
            pass

        return Response(
            {
                "conversation": ConversationSerializer(conversation).data,
                "reply": reply_text,
            },
            status=status.HTTP_200_OK,
        )

class ChatClassificationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        user_input = request.data.get("message", "")
        if not user_input:
            return Response({"error": "Message is required."}, status=400)
        # First, get classification from the model (or fallback)
        gemini_data = generate_safe_reply(user_input)

        # If model returned an error, still try to proceed with any fallback it provided
        if isinstance(gemini_data, dict) and gemini_data.get("error") and not gemini_data.get("fallback"):
            # No useful fallback provided
            return Response(gemini_data, status=status.HTTP_200_OK)

        # Build search terms from classification (use fallback if present)
        classification = gemini_data.get("fallback") if gemini_data.get("fallback") else gemini_data

        search_terms = []
        if "primary_destination" in classification:
            main_loc = classification["primary_destination"].get("location")
            if main_loc:
                search_terms.append(main_loc)

        for suggestion in classification.get("nearby_suggestions", []):
            loc = suggestion.get("location")
            if loc:
                search_terms.append(loc)

        # Only use DB lookups. We will not call any scrapers.
        found_locations, found_homes = [], []

        for term in search_terms:
            loc = Location.objects.filter(
                Q(location_name__icontains=term) |
                Q(city__icontains=term)
            ).first()
            if loc:
                found_locations.append(loc)

            homes = Homes.objects.filter(
                Q(city__icontains=term) | Q(location_name__icontains=term)
            )
            if homes.exists():
                found_homes.extend(list(homes))

        all_locations = list(dict.fromkeys(found_locations))
        all_homes = list(dict.fromkeys(found_homes))

        # If no locations/homes found in DB, persist a lightweight Location/Homes
        # from the Gemini classification so future requests can return a real DB-backed card.
        if not all_locations and not all_homes:
            # classification variable contains either fallback or the raw gemini data
            classified = gemini_data.get("fallback") if gemini_data.get("fallback") else gemini_data
            pd = classified.get("primary_destination") if isinstance(classified, dict) else None
            if pd and pd.get("location"):
                name = pd.get("location").strip()
                desc = pd.get("description") or ""
                # Map additional generated fields from Gemini (if available)
                city = pd.get("city") or pd.get("location_city") or pd.get("region") or name
                country = pd.get("country") or pd.get("location_country")
                best_time = pd.get("best_time_to_visit") or pd.get("best_time")
                avg_cost = None
                try:
                    c = pd.get("average_cost") or pd.get("avg_cost") or pd.get("price")
                    if c is not None:
                        # Strip currency symbols and commas
                        avg_cost = float(str(c).replace("$", "").replace(",", ""))
                except Exception:
                    avg_cost = None

                rating = None
                try:
                    r = pd.get("rating")
                    if r is not None:
                        rating = float(r)
                except Exception:
                    rating = None

                category = pd.get("category") or pd.get("type") or "city"

                # Prefer image provided by Gemini; fallback to Unsplash source
                image_url = None
                if isinstance(pd.get("image"), str) and pd.get("image"):
                    image_url = pd.get("image")
                else:
                    image_url = f"https://source.unsplash.com/featured/?{name.replace(' ', '+')}"

                # Decide whether to create a Homes (hotel) or Location entry using a small heuristic
                lower_msg = (request.data.get('message') or '').lower()
                desc_text = (desc or '').lower()
                hotel_keywords = ["hotel", "stay", "accommodation", "booking", "book", "inn", "resort", "hostel", "bnb", "room", "suite"]
                looks_like_hotel = any(k in lower_msg for k in hotel_keywords) or any(k in desc_text for k in hotel_keywords)

                created_obj = None
                if looks_like_hotel:
                    # Create Homes entry
                    created_obj = Homes.objects.filter(location_name__iexact=name).first()
                    if not created_obj:
                        created_obj = Homes.objects.create(
                            location_name=name,
                            city=city,
                            country=country,
                            description=desc,
                            category=category if category in dict(Homes.CATEGORY_CHOICES) else "city",
                            best_time_to_visit=best_time,
                            average_cost=avg_cost,
                            rating=rating,
                        )
                        # Try to download image and attach
                        try:
                            headers = {"User-Agent": "Mozilla/5.0"}
                            resp = requests.get(image_url, headers=headers, timeout=10)
                            if resp.status_code == 200 and resp.content:
                                filename = f"{slugify(name)[:50]}.jpg"
                                created_obj.location_image.save(filename, ContentFile(resp.content), save=True)
                        except Exception:
                            pass
                    if created_obj:
                        all_homes.append(created_obj)
                else:
                    # Create Location entry
                    created_obj = Location.objects.filter(location_name__iexact=name).first()
                    if not created_obj:
                        created_obj = Location.objects.create(
                            location_name=name,
                            city=city,
                            country=country,
                            description=desc,
                            category=category if category in dict(Location.CATEGORY_CHOICES) else "city",
                            best_time_to_visit=best_time,
                            average_cost=avg_cost,
                            rating=rating,
                        )
                        try:
                            headers = {"User-Agent": "Mozilla/5.0"}
                            resp = requests.get(image_url, headers=headers, timeout=10)
                            if resp.status_code == 200 and resp.content:
                                filename = f"{slugify(name)[:50]}.jpg"
                                created_obj.location_image.save(filename, ContentFile(resp.content), save=True)
                        except Exception:
                            pass
                    if created_obj:
                        all_locations.append(created_obj)

        loc_data = LocationSerializer(all_locations, many=True, context={"request": request}).data
        home_data = HomesSerializer(all_homes, many=True, context={"request": request}).data

        return Response({
            "gemini_classification": gemini_data,
            "matching_locations": loc_data,
            "matching_homes": home_data,
            # scrapers are disabled by design; return empty scraped lists
            "auto_scraped_locations": [],
            "auto_scraped_homes": [],
        }, status=status.HTTP_200_OK)

class ChatSearchView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        user_input = request.data.get("message", "")
        if not user_input:
            return Response({"error": "Message is required."}, status=400)

        gemini_data = generate_safe_reply(user_input)

        if "error" in gemini_data:
            return Response({"error": gemini_data["error"]}, status=500)

        search_terms = []
        if "primary_destination" in gemini_data:
            main_loc = gemini_data["primary_destination"].get("location")
            if main_loc:
                search_terms.append(main_loc)

        for suggestion in gemini_data.get("nearby_suggestions", []):
            loc = suggestion.get("location")
            if loc:
                search_terms.append(loc)

        # Only perform DB lookups; do not call scrapers. If nothing is found,
        # fall back to persisting the Gemini-generated primary_destination.
        found_locations, found_homes = [], []

        for term in search_terms:
            loc = Location.objects.filter(
                Q(location_name__icontains=term) |
                Q(city__icontains=term)
            ).first()
            if loc:
                found_locations.append(loc)

            homes = Homes.objects.filter(
                Q(city__icontains=term) | Q(location_name__icontains=term)
            )
            if homes.exists():
                found_homes.extend(list(homes))

        all_locations = list(dict.fromkeys(found_locations))
        all_homes = list(dict.fromkeys(found_homes))

        # If still empty, attempt to persist a synthetic record from gemini_data
        if not all_locations and not all_homes:
            classified = gemini_data.get("fallback") if gemini_data.get("fallback") else gemini_data
            pd = classified.get("primary_destination") if isinstance(classified, dict) else None
            if pd and pd.get("location"):
                name = pd.get("location").strip()
                desc = pd.get("description") or ""
                city = pd.get("city") or pd.get("location_city") or pd.get("region") or name
                country = pd.get("country") or pd.get("location_country")
                best_time = pd.get("best_time_to_visit") or pd.get("best_time")
                avg_cost = None
                try:
                    c = pd.get("average_cost") or pd.get("avg_cost") or pd.get("price")
                    if c is not None:
                        avg_cost = float(str(c).replace("$", "").replace(",", ""))
                except Exception:
                    avg_cost = None

                rating = None
                try:
                    r = pd.get("rating")
                    if r is not None:
                        rating = float(r)
                except Exception:
                    rating = None

                category = pd.get("category") or pd.get("type") or "city"
                image_url = None
                if isinstance(pd.get("image"), str) and pd.get("image"):
                    image_url = pd.get("image")
                else:
                    image_url = f"https://source.unsplash.com/featured/?{name.replace(' ', '+')}"

                lower_msg = (request.data.get('message') or '').lower()
                desc_text = (desc or '').lower()
                hotel_keywords = ["hotel", "stay", "accommodation", "booking", "book", "inn", "resort", "hostel", "bnb", "room", "suite"]
                looks_like_hotel = any(k in lower_msg for k in hotel_keywords) or any(k in desc_text for k in hotel_keywords)

                created_obj = None
                if looks_like_hotel:
                    created_obj = Homes.objects.filter(location_name__iexact=name).first()
                    if not created_obj:
                        created_obj = Homes.objects.create(
                            location_name=name,
                            city=city,
                            country=country,
                            description=desc,
                            category=category if category in dict(Homes.CATEGORY_CHOICES) else "city",
                            best_time_to_visit=best_time,
                            average_cost=avg_cost,
                            rating=rating,
                        )
                        try:
                            headers = {"User-Agent": "Mozilla/5.0"}
                            resp = requests.get(image_url, headers=headers, timeout=10)
                            if resp.status_code == 200 and resp.content:
                                filename = f"{slugify(name)[:50]}.jpg"
                                created_obj.location_image.save(filename, ContentFile(resp.content), save=True)
                        except Exception:
                            pass
                    if created_obj:
                        all_homes.append(created_obj)
                else:
                    created_obj = Location.objects.filter(location_name__iexact=name).first()
                    if not created_obj:
                        created_obj = Location.objects.create(
                            location_name=name,
                            city=city,
                            country=country,
                            description=desc,
                            category=category if category in dict(Location.CATEGORY_CHOICES) else "city",
                            best_time_to_visit=best_time,
                            average_cost=avg_cost,
                            rating=rating,
                        )
                        try:
                            headers = {"User-Agent": "Mozilla/5.0"}
                            resp = requests.get(image_url, headers=headers, timeout=10)
                            if resp.status_code == 200 and resp.content:
                                filename = f"{slugify(name)[:50]}.jpg"
                                created_obj.location_image.save(filename, ContentFile(resp.content), save=True)
                        except Exception:
                            pass
                    if created_obj:
                        all_locations.append(created_obj)

        loc_data = LocationSerializer(all_locations, many=True).data
        home_data = HomesSerializer(all_homes, many=True).data

        return Response({
            "gemini_classification": gemini_data,
            "matching_locations": loc_data,
            "matching_homes": home_data,
            "auto_scraped_locations": [],
            "auto_scraped_homes": [],
        }, status=status.HTTP_200_OK)
