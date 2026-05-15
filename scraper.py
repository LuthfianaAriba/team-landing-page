import os
import time
import urllib.request
import urllib.parse
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

class MovieScraper:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

        print("Menyiapkan WebDriver...")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
        if not os.path.exists("posters"):
            os.makedirs("posters")

    def scrape_justwatch_data(self, title):
        detail = {
            "synopsis": "No synopsis available.",
            "genre": "N/A",
            "platforms": "Not Available Online",
            "year": "Unknown"
        }
        try:
            search_url = f"https://www.justwatch.com/id/search?q={urllib.parse.quote(title)}"
            self.driver.get(search_url)
            
            first_result = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.title-list-row__column-header, a.title-card-link"))
            )
            self.driver.get(first_result.get_attribute("href"))
            time.sleep(2) 

            # 1. AMBIL SYNOPSIS
            try:
                synopsis_el = self.driver.find_element(By.CSS_SELECTOR, "#synopsis p, p.text-wrap-pre-line.mt-0")
                if synopsis_el.text.strip(): 
                    detail["synopsis"] = synopsis_el.text.strip()
            except: pass

            # 2. AMBIL GENRE
            try:
                headings = self.driver.find_elements(By.CSS_SELECTOR, "h3.detail-infos__subheading")
                for heading in headings:
                    if "Genre" in heading.text:
                        parent = heading.find_element(By.XPATH, "..")
                        value_div = parent.find_element(By.CSS_SELECTOR, "div.detail-infos__value")
                        detail["genre"] = value_div.text.strip()
                        break
            except: pass

            # 3. AMBIL TAHUN (Sebagai Backup kalau IMDb gagal)
            try:
                year_el = self.driver.find_element(By.CSS_SELECTOR, "div.title-block span.text-muted")
                year_text = year_el.text.replace("(", "").replace(")", "").strip()
                if year_text.isdigit():
                    detail["year"] = year_text
            except: pass

            # 4. AMBIL PLATFORM (MURNI TEKS)
            try:
                logo_elements = self.driver.find_elements(By.CSS_SELECTOR, "img.provider-icon")
                nama_platform_list = []
                for logo in logo_elements:
                    nama_platform = logo.get_attribute("alt")
                    if nama_platform and nama_platform not in nama_platform_list:
                        nama_platform_list.append(nama_platform)
                
                if nama_platform_list:
                    detail["platforms"] = ", ".join(nama_platform_list)
            except: pass

        except Exception as e:
            print(f"Info JustWatch tidak ditemukan untuk '{title}': {e}")

        return detail

    def _get_movie_details(self, url):
        try:
            self.driver.get(url)
            script_tag = self.wait.until(EC.presence_of_element_located((By.XPATH, "//script[@type='application/ld+json']")))
            json_text = script_tag.get_attribute("innerHTML")
            data = json.loads(json_text)
            
            title = data.get("name", "Unknown Title")
            genre_raw = data.get("genre", ["General"])
            genre = ", ".join(genre_raw) if isinstance(genre_raw, list) else genre_raw
            year = data.get("datePublished", "Unknown").split("-")[0] if "datePublished" in data else "Unknown"
            rating = str(data.get("aggregateRating", {}).get("ratingValue", "N/A"))
            votes  = str(data.get("aggregateRating", {}).get("ratingCount", "0"))  # FIX: ambil jumlah votes
            poster = data.get("image", "")

            return {
                "title": title, "year": year, "genre": genre, "rating": rating,
                "votes": votes,   # FIX: simpan votes ke data film
                "poster_url": poster, "status": "Plan to Watch"
            }
        except Exception as e:
            return {"error": str(e)}

    def scrape_top_movies(self, limit=20):
        print(f"Memulai bulk-scraping {limit} film teratas...")
        hasil_list = []
        try:
            self.driver.get("https://www.imdb.com/chart/top/")
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.ipc-metadata-list-summary-item")))
            links = self.driver.find_elements(By.CSS_SELECTOR, "a.ipc-title-link-wrapper")
            urls = [link.get_attribute("href") for link in links[:limit]]
            
            for i, url in enumerate(urls):
                print(f"Scraping film {i+1}/{limit}...")
                detail = self._get_movie_details(url)
                
                if "error" not in detail:
                    title = detail.get("title", "")
                    jw_data = self.scrape_justwatch_data(title)
                    
                    detail["description"] = jw_data["synopsis"]
                    detail["platform_string"] = jw_data["platforms"]
                    
                    if jw_data.get("genre") != "N/A":
                        detail["genre"] = jw_data["genre"]
                        
                    # Fix Tahun: Gunakan tahun JustWatch kalau IMDb gagal
                    if detail.get("year") == "Unknown" and jw_data.get("year") != "Unknown":
                        detail["year"] = jw_data["year"]
                    
                    # Download Poster
                    img_url = detail.get("poster_url")
                    if img_url and img_url.startswith("http"):
                        safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
                        local_path = f"posters/{safe_title.replace(' ', '_')}.jpg"
                        try:
                            req = urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0'})
                            with urllib.request.urlopen(req, timeout=5) as response, open(local_path, 'wb') as out_file:
                                out_file.write(response.read())
                            detail["poster_local"] = local_path
                        except Exception:
                            detail["poster_local"] = ""
                    
                    detail.pop("poster_url", None)
                    hasil_list.append(detail)
            
            return hasil_list
        except Exception as e:
            print(f"Gagal mengambil Top Movies: {e}")
            return hasil_list

    def search_movie(self, query):
        pass

    def close(self):
        self.driver.quit()
