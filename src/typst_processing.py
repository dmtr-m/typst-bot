import tempfile
import typst
from pdf2image import convert_from_bytes
from PIL import Image, ImageChops, ImageOps
from io import BytesIO

typst_template = """
#set align(center + horizon)
#set page(
    paper: "a6",
    flipped: true,
    margin: auto
)
"""


def typ_to_pdf(typ_string: str) -> bytes:
    """
    Converts typst style string into pdf_bytes
    input: string (typ)
    output: bytes (pdf)
    """
    typst_temp_file = tempfile.NamedTemporaryFile()
    typ_string = typst_template + typ_string
    typst_to_convert = bytes(typ_string, 'utf-8')
    typst_temp_file.write(typst_to_convert)
    typst_temp_file.seek(0)
    typst_pdf_bytes = typst.compile(typst_temp_file.name)
    typst_temp_file.close()
    return typst_pdf_bytes


def pdf_to_image(pdf_bytes: bytes) -> bytes:
    """
    Converts pdf bytes into png bytes
    input: bytes (pdf)
    output: bytes (png)
    """
    image_temp_file = tempfile.NamedTemporaryFile()
    images = convert_from_bytes(pdf_bytes, dpi=400)
    images[0].save(image_temp_file, 'PNG')
    image_temp_file.seek(0)
    return image_temp_file.read()


def remove_whitespaces(image_bytes: bytes) -> Image:
    """
    Removes whitespaces, so that image ends right where formula does
    receives image with borders
    returns image with no borders
    input: bytes (png)
    output: Image (PIL object)
    """
    image = Image.open(BytesIO(image_bytes))
    bg = Image.new(image.mode, image.size, image.getpixel((0, 0)))
    diff = ImageChops.difference(image, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    image = image.crop(bbox)
    if bbox:
        return image


def calculate_borders(image_size: (int, int)) -> (int, int):
    """
    Calculates borders for image.
    Sets borders to a range within 3/1 to 1/3.
    receives a tuple (width, height) wtih properties of an image
    returns a tuple (width_border, height_border) with properties of borders
    input: (int, int)
    output: (int, int)
    """
    MINIMUM_BORDER_SIZE = 0.2 # 20 percent
    width, height = image_size

    if width/height > 3/1:
        # If image is too wide
        # Add minimum borders to width
        # Set height so that ration is 3/1
        width_border = width * MINIMUM_BORDER_SIZE
        height_border = ((width + 2*width_border) // 3 - height) // 2
    elif 3 / 1 >= width/height >= 1 / 3:
        # This is a great ratio, leave it as it is
        width_border = width * MINIMUM_BORDER_SIZE
        height_border = height * MINIMUM_BORDER_SIZE
    else:
        # If image is too thin
        # Add minimum borders to height
        # Set width so that ratio is 1/3
        height_border = height * MINIMUM_BORDER_SIZE
        width_border = ((height + 2*height_border) // 3 - width) // 2

    return (int(width_border), int(height_border))


def set_new_borders(image: Image) -> Image:
    """
    Expands image with new whitespaces with better ratio
    receives PIL image
    returns PIL image with improved resolution
    input: Image (PIL)
    output: Image (PIL)
    """
    # Adding borders
    size = image.size
    borders = calculate_borders(size)
    image = ImageOps.expand(image, border=borders, fill='white')
    # Writing image
    return image


def resize_image(image: Image) -> Image:
    """
    Setting to an optimal telegram size 1280*1280 if needed
    receives PIL image with no borders
    returns PIL image with better borders
    input: Image (PIL)
    output: Image (PIL)
    """
    width, height = image.size
    if width > 1280 or height > 1280:
        size_decrease_k = 1280 / max(width, height)
        new_size = int(width * size_decrease_k), int(height * size_decrease_k)
        image = image.resize(new_size)
    return image


def beautify_image(image_bytes: bytes) -> (bytes, tuple):
    """
    Setting width to height ratio to a range between 1/3 and 3/1
    Resizing to a max 1280*1280.
    receives png bytes of raw image
    returns png bytes of a modified image
    input: bytes (png)
    output: bytes (png)
    """
    image_with_no_borders = remove_whitespaces(image_bytes)
    image_with_imporved_borders = set_new_borders(image_with_no_borders)
    resized_image = resize_image(image_with_imporved_borders)

    image_bytes = BytesIO()
    resized_image.save(image_bytes, format='PNG')
    size = resized_image.size
    # For debug purposes.
    # To write image to file uncomment this
    # image.save('test.png', format='PNG')
    return image_bytes.getvalue(), size


def generate_image(typ_query: str):
    """
    Does the whole process; from typ to image
    input: str (typ)
    output: bytes (png), tuple
    """
    typ_query = f"$ {typ_query} $"
    pdf = typ_to_pdf(typ_query)
    img = pdf_to_image(pdf)
    img_and_size = beautify_image(img)
    return img_and_size


if __name__ == '__main__':
    status, pdf = typ_to_pdf('""')
    print(status)
    status, image_bytes = pdf_to_image(pdf)
    print(status)
    status, image_bytes = beautify_image(image_bytes)
    print(status)