import os
import json
import time
import google.generativeai as genai
from PIL import Image, ImageDraw
from typing import List, Optional
from pydantic import BaseModel, Field
from google.api_core.exceptions import ResourceExhausted

class UIElement(BaseModel):
    name: str = Field(description="A short, descriptive name of the element")
    type: str = Field(description="The type of the element, such as button, menu, icon, spreadsheet cell, column header, or row header")
    text: Optional[str] = Field(description="The visible text content of the element, if applicable")
    bbox: List[int] = Field(description="The bounding box coordinates [ymin, xmin, ymax, xmax] as integers from 0 to 1000 representing normalized coordinates (0 is top/left, 1000 is bottom/right)")

class UIAnalysis(BaseModel):
    elements: List[UIElement] = Field(description="A list of the smallest visible UI elements found in the screenshot")

# 1. Configure the Gemini API client
# Make sure to set the GEMINI_API_KEY environment variable.
genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))

# Directories
input_dir = "Dismal"
annotated_dir = "Dismal_annotated"
json_dir = "Dismal_json"

os.makedirs(annotated_dir, exist_ok=True)
os.makedirs(json_dir, exist_ok=True)

# 2. Initialize the model
model = genai.GenerativeModel('gemini-3.1-pro-preview')

prompt = """
Analyze this UI screenshot.

Return only stable visible UI elements:
- top menu items
- toolbar buttons/icons
- spreadsheet column headers
- spreadsheet row headers
- non-empty spreadsheet cells
- status/mode-line regions

Do not return individual characters.
Do not return red annotation labels or red rectangles if present.
Do not infer hidden cells.
Use bbox as [ymin, xmin, ymax, xmax], normalized 0 to 1000.
Return JSON only.
"""

def process_image(image_path, filename):
    print(f"\nProcessing {filename}...")
    try:
        img = Image.open(image_path).convert("RGB")
    except Exception as e:
        print(f"Failed to open image {filename}: {e}")
        return

    img_width, img_height = img.size
    
    # Retry logic for rate limiting / quota exhaustion
    max_retries = 10
    response_text = None
    
    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                [prompt, img],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.0,
                    response_mime_type="application/json",
                    response_schema=UIAnalysis,
                ),
            )
            response_text = response.text
            break  # Success
            
        except ResourceExhausted:
            wait_time = 60
            print(f"Rate limit or quota hit. Waiting {wait_time} seconds before retry {attempt + 1}/{max_retries}...")
            time.sleep(wait_time)
        except Exception as e:
            if '429' in str(e) or 'quota' in str(e).lower():
                wait_time = 60
                print(f"Rate limit hit. Waiting {wait_time} seconds before retry {attempt + 1}/{max_retries}...")
                time.sleep(wait_time)
            else:
                print(f"Failed to process {filename}: {e}")
                return

    if not response_text:
        print(f"Could not get a successful response for {filename} after {max_retries} attempts.")
        return

    try:
        # Parse the JSON response
        data = json.loads(response_text)
        elements = data.get("elements", [])

        # Draw bounding boxes
        draw = ImageDraw.Draw(img)
        for item in elements:
            name = item.get("name", "Unknown")
            bbox = item.get("bbox")

            if isinstance(bbox, list) and len(bbox) == 4:
                ymin, xmin, ymax, xmax = bbox
                abs_ymin = (ymin / 1000.0) * img_height
                abs_xmin = (xmin / 1000.0) * img_width
                abs_ymax = (ymax / 1000.0) * img_height
                abs_xmax = (xmax / 1000.0) * img_width
                
                draw.rectangle([abs_xmin, abs_ymin, abs_xmax, abs_ymax], outline="red", width=3)
                text_pos = (abs_xmin, max(0, abs_ymin - 15))
                draw.text(text_pos, name, fill="red")

        base_name = os.path.splitext(filename)[0]
        
        # Save JSON
        json_output_path = os.path.join(json_dir, f"{base_name}.json")
        with open(json_output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            
        # Save annotated image
        output_img_path = os.path.join(annotated_dir, f"{base_name}.png")
        img.save(output_img_path)
        
        print(f"Saved annotations to {json_output_path}")
        print(f"Saved image to {output_img_path}")

    except json.JSONDecodeError:
        print(f"Failed to parse JSON for {filename}. Model output was:\n{response_text}")
    except Exception as e:
        print(f"An error occurred while saving {filename}: {e}")

def main():
    if not os.path.exists(input_dir):
        print(f"Directory '{input_dir}' not found.")
        return
        
    supported_formats = (".png", ".jpg", ".jpeg", ".webp")
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(supported_formats) and "step0" in filename.lower():
            image_path = os.path.join(input_dir, filename)
            process_image(image_path, filename)
            
            # Brief pause between successful requests to be friendly to rate limits
            time.sleep(2)

if __name__ == "__main__":
    main()
