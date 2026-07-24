import base64
import json
import re
from openai import OpenAI
from PIL import Image, ImageDraw

# 1. Helper function to encode your local image into a Base64 string
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# 2. Initialize the client pointing to your Ngrok tunnel
client = OpenAI(
    base_url="https://dishearteningly-undefendable-ross.ngrok-free.dev/v1", # Replace with your actual Ngrok URL
    api_key="sk-no-key-required" 
)

# 3. Encode the image
image_path = "Picture2.png" # Change this to the path of your image
base64_image = encode_image(image_path)

print("Sending image to Colab server...")

# We ask the model to strictly return JSON containing bounding box info
prompt = """
Do not think. Return only valid JSON.

Analyze the UI screenshot and return a JSON array of visible UI elements. I want UI breakdown to the smallest visible elements.

Each item must have this exact format:
{
  "name": "short element name",
  "type": "button/textbox/menu/icon/text/other",
  "bbox": [xmin, ymin, xmax, ymax]
}

Rules:
- Return only the JSON array.
- Do not use markdown.
- Do not explain.
- Coordinates must be pixel coordinates relative to the original image.
"""
# 4. Make the request
response = client.chat.completions.create(
    model="default",
    temperature=0.0,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"
                    }
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }
    ],
    max_tokens=4096,
    extra_body={
        "reasoning_format": "none",
        "chat_template_kwargs": {
            "enable_thinking": False
        }
    }
)

raw = response.model_dump()
print("\nFull raw response:")
print("=========================================")
print(json.dumps(raw, indent=2))

msg = raw["choices"][0]["message"]

response_text = (
    msg.get("content")
    or msg.get("reasoning_content")
    or msg.get("reasoning")
    or ""
)

print("\nExtracted Model Response:")
print("=========================================")
print(response_text)

if not response_text.strip():
    raise ValueError("Model returned empty visible text. Check reasoning fields or increase max_tokens.")

try:
    json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
    if json_match:
        elements = json.loads(json_match.group(0))
    else:
        elements = json.loads(response_text)

    print("\nDrawing bounding boxes...")
    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)

    for item in elements:
        name = item.get("name", "Unknown")
        bbox = item.get("bbox")

        if isinstance(bbox, list) and len(bbox) == 4:
            bbox = [int(x) for x in bbox]
            draw.rectangle(bbox, outline="red", width=3)
            text_pos = (bbox[0], max(0, bbox[1] - 15))
            draw.text(text_pos, name, fill="red")

    output_path = "annotated_image.jpg"
    img.save(output_path)
    print(f"Annotated image saved to: {output_path}")
    img.show()

except json.JSONDecodeError:
    print("\nFailed to parse JSON.")
    print("Model output was:")
    print(response_text)