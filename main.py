from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import time
import csv

app = FastAPI()

# Define the data model for the request body
class ScrapeRequest(BaseModel):
    url: str
    output_file: str

# Function to perform the web scraping
def scrape_data(url: str, output_file: str):
    options = webdriver.ChromeOptions()
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--disable-extensions")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    options.add_argument("--disable-features=SameSiteByDefaultCookies,CookiesWithoutSameSiteMustBeSecure")

    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(2)

    state_dropdown = driver.find_element(By.ID, "stateId")
    state_options = Select(state_dropdown).options

    with open(output_file, 'a', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['Name of BC', 'Contact Number', 'Gender', 'Bank Name', 'State', 'District', 'Block', 'Pincode', 'Corporate', 'Gram Panchayat(GP)', 'Village Name', 'Corporate BC Name'])

        for i in range(1, len(state_options)):
            state_options[i].click()
            time.sleep(2)
            district_dropdown = driver.find_element(By.ID, "districtId")
            district_options = Select(district_dropdown).options

            for j in range(1, len(district_options)):
                district_options[j].click()
                button = driver.find_elements(By.CLASS_NAME, "search_btn")[-2]
                driver.execute_script("arguments[0].click();", button)
                time.sleep(2)

                captcha = driver.find_element(By.ID, "txtCaptcha_search")
                captcha_text = captcha.get_attribute("value").replace(" ", "")
                captcha_input = driver.find_element(By.ID, "cap_search")
                captcha_input.send_keys(captcha_text)

                button_xpath = "//a[@type='submit' and text()='Verify']"
                button = driver.find_element(By.XPATH, button_xpath)
                driver.execute_script("arguments[0].click();", button)
                time.sleep(5)

                table = driver.find_element(By.TAG_NAME, "table")
                table_body = table.find_element(By.TAG_NAME, "tbody")
                rows = table_body.find_elements(By.TAG_NAME, "tr")

                for row in rows:
                    second_cell = row.find_elements(By.TAG_NAME, "td")[1]
                    anchor_tag = second_cell.find_element(By.TAG_NAME, "a")
                    driver.execute_script("arguments[0].click();", anchor_tag)
                    time.sleep(2)

                    captcha = driver.find_element(By.ID, "txtCaptcha_detail")
                    captcha_text = captcha.get_attribute("value").replace(" ", "")
                    captcha_input = driver.find_element(By.ID, "cap_detail")
                    captcha_input.send_keys(captcha_text)

                    button_xpath = "//a[@type='submit' and text()='Verify']"
                    button = driver.find_element(By.XPATH, button_xpath)
                    driver.execute_script("arguments[0].click();", button)
                    time.sleep(2)

                    modal = driver.find_element(By.ID, "modelcontentDiv")
                    modal_table = modal.find_element(By.TAG_NAME, "tbody")
                    modal_rows = modal_table.find_elements(By.TAG_NAME, "tr")

                    data = []
                    for modal_row in modal_rows:
                        modal_cells = modal_row.find_elements(By.TAG_NAME, "td")
                        data.append(modal_cells[1].text)
                    
                    writer.writerow(data)
                
                driver.back()
                time.sleep(4)
                state_dropdown = driver.find_element(By.ID, "stateId")
                state_options = Select(state_dropdown).options
                state_options[i].click()
                time.sleep(2)
                district_dropdown = driver.find_element(By.ID, "districtId")
                district_options = Select(district_dropdown).options

        time.sleep(2)
        state_dropdown = driver.find_element(By.ID, "stateId")
        state_options = Select(state_dropdown).options

    driver.quit()

@app.post("/scrape/")
async def start_scraping(scrape_request: ScrapeRequest, background_tasks: BackgroundTasks):
    try:
        background_tasks.add_task(scrape_data, scrape_request.url, scrape_request.output_file)
        return {"message": "Scraping started!", "output_file": scrape_request.output_file}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
