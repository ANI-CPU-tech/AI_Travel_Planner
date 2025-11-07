from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from .models import Plan
from .serializers import PlanSerializer, PlanCreateSerializer
from assistant.services import generate_plan
import json
from Location.models import Location, Homes
from django.core.files.base import ContentFile
from django.utils.text import slugify
import requests


class PlanViewSet(viewsets.ModelViewSet):
    queryset = Plan.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ("create", "generate"):
            return PlanCreateSerializer
        return PlanSerializer

    def get_queryset(self):
        # Users only see their own plans
        user = self.request.user
        return Plan.objects.filter(user=user)

    def perform_create(self, serializer):
        plan = serializer.save(user=self.request.user)
        # After saving the Plan, try to persist referenced places into Location/Homes
        self._attach_places_from_itinerary(plan)

    def _attach_places_from_itinerary(self, plan: Plan):
        itinerary = plan.itinerary or {}
        # Expect itinerary to contain list under 'itinerary'
        days = itinerary.get("itinerary") if isinstance(itinerary, dict) else None
        if not days and isinstance(plan.itinerary, list):
            days = plan.itinerary

        if not days:
            return

        for day in days:
            activities = day.get("activities") or []
            for act in activities:
                try:
                    typ = (act.get("type") or "location").lower()
                    name = (act.get("name") or "").strip()
                    desc = act.get("description") or ""
                    image = act.get("image")
                    avg = act.get("average_cost")
                    rating = act.get("rating")

                    if not name:
                        continue

                    if typ in ("hotel", "home", "accommodation"): 
                        obj = Homes.objects.filter(location_name__iexact=name).first()
                        if not obj:
                            obj = Homes.objects.create(
                                location_name=name,
                                city=name,
                                description=desc,
                                average_cost=avg,
                                rating=rating,
                                category="city",
                            )
                            # try to download image
                            if image and isinstance(image, str) and image.startswith("http"):
                                try:
                                    resp = requests.get(image, timeout=10, headers={"User-Agent":"Mozilla/5.0"})
                                    if resp.status_code == 200 and resp.content:
                                        filename = f"{slugify(name)[:50]}.jpg"
                                        obj.location_image.save(filename, ContentFile(resp.content), save=True)
                                except Exception:
                                    pass
                        plan.homes.add(obj)
                    else:
                        obj = Location.objects.filter(location_name__iexact=name).first()
                        if not obj:
                            obj = Location.objects.create(
                                location_name=name,
                                city=name,
                                description=desc,
                                average_cost=avg,
                                rating=rating,
                                category="city",
                            )
                            if image and isinstance(image, str) and image.startswith("http"):
                                try:
                                    resp = requests.get(image, timeout=10, headers={"User-Agent":"Mozilla/5.0"})
                                    if resp.status_code == 200 and resp.content:
                                        filename = f"{slugify(name)[:50]}.jpg"
                                        obj.location_image.save(filename, ContentFile(resp.content), save=True)
                                except Exception:
                                    pass
                        plan.locations.add(obj)
                except Exception:
                    continue

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def generate(self, request):
        """Generate a plan with Gemini for the user's prompt (returns JSON plan, not persisted).
        The frontend can use this to show a plan preview and then call the create endpoint to save it.
        """
        message = request.data.get("message")
        if not message:
            return Response({"error": "message is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            plan_data = generate_plan(message)

            # If the model returned raw_text that contains embedded JSON, try to parse it here
            if isinstance(plan_data, dict) and plan_data.get('raw_text'):
                raw = plan_data.get('raw_text')
                try:
                    # attempt to parse any JSON substring
                    first = raw.find('{')
                    last = raw.rfind('}')
                    if first != -1 and last != -1 and last > first:
                        plan_data = json.loads(raw[first:last+1])
                    else:
                        plan_data = json.loads(raw)
                except Exception:
                    # leave plan_data as-is (will fall back below)
                    pass

            # Validate shape: we expect a dict with an 'itinerary' list (or dict) and optional 'summary'
            valid = isinstance(plan_data, dict) and (
                isinstance(plan_data.get('itinerary'), list) or isinstance(plan_data.get('itinerary'), dict) or 'itinerary' in plan_data
            )

            if not valid:
                # treat as failure and raise to hit fallback below
                raise ValueError("Generated plan did not follow expected schema")

            # If the user is authenticated, persist the generated plan immediately
            if request.user and request.user.is_authenticated:
                serializer = PlanCreateSerializer(data={
                    'title': plan_data.get('summary')[:80] if plan_data.get('summary') else '',
                    'start_date': plan_data.get('start_date') or None,
                    'end_date': plan_data.get('end_date') or None,
                    'num_days': len(plan_data.get('itinerary')) if isinstance(plan_data.get('itinerary'), list) else None,
                    'summary': plan_data.get('summary') or '',
                    'itinerary': plan_data,
                })
                serializer.is_valid(raise_exception=True)
                plan = serializer.save(user=request.user)
                # attach places referenced in the plan
                self._attach_places_from_itinerary(plan)
                return Response(PlanSerializer(plan, context={'request': request}).data, status=status.HTTP_201_CREATED)

            # anonymous preview response
            return Response(plan_data, status=status.HTTP_200_OK)
        except Exception as e:
            # If Gemini is not available (missing API key or quota), return a deterministic fallback plan
            # Try to extract basic pieces: destination, days, budget
            import re
            from assistant.services import heuristic_classify

            dest = None
            days = None
            budget = None

            # heuristic classification for destination
            try:
                hc = heuristic_classify(message)
                pd = hc.get("primary_destination") or {}
                dest = pd.get("location")
            except Exception:
                dest = None

            # find numbers for days and rupee amounts
            m_days = re.search(r"(\d+)\s*(?:days|day)", message, re.IGNORECASE)
            if m_days:
                try:
                    days = int(m_days.group(1))
                except Exception:
                    days = None

            m_budget = re.search(r"(\d+[\d,]*)\s*(?:rupees|rs|inr|₹)", message, re.IGNORECASE)
            if m_budget:
                try:
                    budget = float(m_budget.group(1).replace(",", ""))
                except Exception:
                    budget = None

            # default days
            if not days:
                days = 3

            summary = f"Suggested {days}-day plan for {dest or 'your destination'}"
            itinerary = []
            # simple archetype activities for Mysuru-like heritage city
            archetype = [
                "Visit the royal palace and museum",
                "Explore local gardens and zoo / Lalbagh-like sites",
                "Visit markets, craft shops and try local cuisine",
                "See prominent temples and cultural evening program",
            ]
            for i in range(days):
                act_name = archetype[i % len(archetype)]
                itinerary.append({
                    "day": i + 1,
                    "date": None,
                    "activities": [
                        {
                            "type": "location",
                            "name": act_name,
                            "description": f"Suggested activity: {act_name} in {dest or ''}",
                            "image": None,
                            "average_cost": round((budget / days) if budget else None, 2) if budget else None,
                            "rating": None,
                        }
                    ]
                })

            fallback = {
                "summary": summary,
                "start_date": None,
                "end_date": None,
                "itinerary": itinerary,
            }

            return Response({"fallback": fallback, "error": str(e)}, status=status.HTTP_200_OK)
from django.shortcuts import render

# Create your views here.
