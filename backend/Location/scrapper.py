# Location/scraper.py
import requests
from bs4 import BeautifulSoup
from .models import Location, Homes
from decimal import Decimal
from django.core.files.base import ContentFile
from django.utils.text import slugify

HEADERS = {"User-Agent": "Mozilla/5.0"}
import re

PRICE_RE = re.compile(r"(\d[\d,\. ]*)")

def extract_price_number(text: str):
    """
    Extract a numeric price from arbitrary text like '₹ 12,499 per night' or '$180'.
    Returns Decimal or None.
    """
    if not text:
        return None
    m = PRICE_RE.search(str(text))
    if not m:
        return None
    digits = re.sub(r"[^\d.]", "", m.group(1))  # keep digits and dot
    try:
        # prefer integer magnitude (Holidify usually INR integers)
        from decimal import Decimal
        if digits.count(".") > 1:
            # too many dots, fallback to stripping dots
            digits = digits.replace(".", "")
        return Decimal(digits)
    except Exception:
        return None

# -------------------- LOCATION SCRAPER --------------------
def scrape_holidify_location(query: str):
    """
    Scrape Holidify for details about a given location.
    Returns a Location object (created or fetched).
    """
    try:
        url = f"https://www.holidify.com/places/{query.lower().replace(' ', '-')}/"
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            print(f"[SCRAPER] Failed to fetch {url}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        # Description
        desc_tag = soup.find("meta", {"name": "description"})
        description = desc_tag["content"] if desc_tag else "No description available."

        # Image
        image_tag = soup.find("meta", {"property": "og:image"})
        image_url = image_tag["content"] if image_tag else None

        # Guess category based on text
        category_guess = "nature"
        desc_lower = description.lower()
        if "beach" in desc_lower:
            category_guess = "beach"
        elif "city" in desc_lower:
            category_guess = "city"
        elif "hill" in desc_lower or "mountain" in desc_lower:
            category_guess = "adventure"
        elif "romantic" in desc_lower:
            category_guess = "romantic"
        elif "wildlife" in desc_lower:
            category_guess = "wildlife"

        location, created = Location.objects.get_or_create(
            location_name=query.title(),
            defaults={
                "country": "",
                "city": query.title(),
                "description": description,
                "category": category_guess,
                "average_cost": None,
                "rating": None,
            },
        )
        # If an image URL was discovered, try to download and save it to the ImageField
        if image_url and created and not location.location_image:
            try:
                resp = requests.get(image_url, headers=HEADERS, timeout=10)
                if resp.status_code == 200 and resp.content:
                    filename = f"{slugify(query)[:50]}.jpg"
                    location.location_image.save(filename, ContentFile(resp.content), save=True)
            except Exception:
                pass
        print(f"[SCRAPER] Location added/updated: {query.title()}")
        return location

    except Exception as e:
        print(f"[SCRAPER ERROR - Location] {e}")
        return None


# -------------------- HOTEL/HOME SCRAPER --------------------

def scrape_holidify_hotels_json(city: str):
    """
    Fetch hotels from Holidify's internal JSON API.
    Returns a list[Homes].
    """
    try:
        slug = city.lower().replace(" ", "-")
        url = f"https://www.holidify.com/api/v1/hotels/{slug}/"
        resp = requests.get(url, headers=HEADERS, timeout=12)
        if resp.status_code != 200:
            print(f"[SCRAPER][Holidify JSON] {city}: HTTP {resp.status_code}")
            return []

        data = resp.json()
        hotels = data.get("data", {}).get("hotels", []) or []
        scraped = []

        for h in hotels[:12]:
            name = (h.get("name") or "").strip()
            if not name:
                continue

            desc = h.get("description") or f"Hotel in {city.title()} (Holidify)."
            image = h.get("image")
            rating = h.get("rating")

            # Holidify returns strings like "₹ 12,499"
            price_text = (h.get("price") or h.get("priceText") or "").strip()
            avg_cost = extract_price_number(price_text)

            home, created = Homes.objects.update_or_create(
                location_name=name,
                city=city.title(),
                defaults={
                    "country": "",
                    "description": desc,
                    "category": "city",
                    "best_time_to_visit": "",
                    "average_cost": avg_cost,
                    "rating": rating,
                },
            )
            # If Holidify returned an image URL and we created a new record, try to download it
            if image and created and not home.location_image:
                try:
                    resp = requests.get(image, headers=HEADERS, timeout=10)
                    if resp.status_code == 200 and resp.content:
                        filename = f"{slugify(name)[:50]}.jpg"
                        home.location_image.save(filename, ContentFile(resp.content), save=True)
                except Exception:
                    pass
            scraped.append(home)

        return scraped

    except Exception as e:
        print(f"[SCRAPER][Holidify JSON] {city}: {e}")
        return []



# ---------- SOURCE B: TripAdvisor via Playwright (fallback) ----------
def scrape_tripadvisor_hotels_playwright(city: str):
    """
    Headless scrape of TripAdvisor hotel listing for a city.
    Falls back from /Search to a Hotels listing page if we can click through.
    Returns list[Homes].
    """
    try:
        from playwright.sync_api import sync_playwright

        query = city.lower().replace(" ", "+") + "+hotels"
        start_url = f"https://www.tripadvisor.in/Search?q={query}"

        scraped = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
                viewport={"width": 1366, "height": 900},
                java_script_enabled=True,
            )
            page = context.new_page()
            page.goto(start_url, wait_until="domcontentloaded", timeout=45000)

            # Best-effort cookies
            try:
                page.locator("button:has-text('Accept')").first.click(timeout=2000)
            except:
                pass

            # Try to find a Hotels listing link and click it (more reliable than parsing the search page)
            try:
                # any link that looks like a Hotels listing for this city
                hotels_link = page.locator("a[href*='/Hotels-']").first
                if hotels_link.count():
                    href = hotels_link.get_attribute("href")
                    if href:
                        target = href if href.startswith("http") else f"https://www.tripadvisor.in{href}"
                        page.goto(target, wait_until="domcontentloaded", timeout=45000)
            except:
                pass

            # Now try to parse cards on the listing page
            # Stable container:
            try:
                page.wait_for_selector("[data-test-target='HR_CC_CARD']", timeout=12000)
            except:
                print(f"[SCRAPER][TA] No listing cards for {city}")
                context.close(); browser.close()
                return []

            cards = page.locator("[data-test-target='HR_CC_CARD']")
            count = min(cards.count(), 12)

            for i in range(count):
                card = cards.nth(i)

                # Name
                name = ""
                try:
                    name = card.locator("a[data-test-target='property-card-name']").inner_text().strip()
                except:
                    pass
                if not name:
                    continue

                # Rating: aria-label like "4.5 of 5 bubbles"
                rating = None
                try:
                    aria = card.locator("span[aria-label*='of 5 bubbles']").first.get_attribute("aria-label") or ""
                    m = re.search(r"([\d\.]+)\s+of\s+5", aria)
                    if m:
                        from decimal import Decimal
                        rating = Decimal(m.group(1))
                except:
                    pass

                # Price: common blocks
                price_text = None
                try:
                    # Try dedicated price target first
                    price_node = card.locator("[data-test-target='price']").first
                    if not price_node.count():
                        price_node = card.locator("span[class*=price], div[class*=price]").first
                    if price_node.count():
                        price_text = price_node.inner_text().strip()
                except:
                    pass

                avg_cost = extract_price_number(price_text)

                # Image
                image_url = None
                try:
                    img = card.locator("img").first
                    image_url = img.get_attribute("src") or img.get_attribute("data-src") if img.count() else None
                except:
                    pass

                desc = f"Hotel in {city.title()} (TripAdvisor)."

                home, created = Homes.objects.update_or_create(
                    location_name=name,
                    city=city.title(),
                    defaults={
                        "country": "",
                        "description": desc,
                        "category": "city",
                        "best_time_to_visit": "",
                        "average_cost": avg_cost,
                        "rating": rating,
                    },
                )
                # If TripAdvisor provided an image URL and we created the record, download it
                if image_url and created and not home.location_image:
                    try:
                        resp = requests.get(image_url, headers=HEADERS, timeout=10)
                        if resp.status_code == 200 and resp.content:
                            filename = f"{slugify(name)[:50]}.jpg"
                            home.location_image.save(filename, ContentFile(resp.content), save=True)
                    except Exception:
                        pass
                scraped.append(home)

            context.close()
            browser.close()

        return scraped

    except Exception as e:
        print(f"[SCRAPER][TA:Playwright] {city}: {e}")
        return []


# ---------- WRAPPER: Dual-source ----------
def scrape_hotels_dual(city: str):
    """
    Dual-source strategy:
    1) Holidify JSON first
    2) If none found -> TripAdvisor (Playwright) fallback
    Returns list[Homes].
    """
    # Fast path
    holidify_results = scrape_holidify_hotels_json(city)
    if holidify_results:
        print(f"[SCRAPER] Holidify provided {len(holidify_results)} hotels for {city}")
        return holidify_results

    # Fallback
    print(f"[SCRAPER] Holidify empty for {city}. Falling back to TripAdvisor (Playwright)…")
    ta_results = scrape_tripadvisor_hotels_playwright(city)
    if ta_results:
        print(f"[SCRAPER] TripAdvisor provided {len(ta_results)} hotels for {city}")
    else:
        print(f"[SCRAPER] TripAdvisor also empty for {city}")
    return ta_results