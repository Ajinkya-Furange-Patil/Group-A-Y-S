import re
import base64
from PIL import Image
from io import BytesIO

with open('rendered_dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

match = re.search(r'src=\"data:image/png;base64,([^\"]+)\" alt=\"Company Logo\"', content)
if match:
    b64 = match.group(1)
    # Remove any newlines from b64 string
    b64 = b64.replace('\n', '')
    img_data = base64.b64decode(b64)
    img = Image.open(BytesIO(img_data))
    img.save('logo.ico', format='ICO')
    print('Saved logo.ico')
else:
    print('Logo not found')
