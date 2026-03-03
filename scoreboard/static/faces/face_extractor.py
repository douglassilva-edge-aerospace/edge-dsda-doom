import os
import struct
from PIL import Image

def load_palette(pal_path):
    """Reads the first 768 bytes of PLAYPAL to get the RGB palette."""
    with open(pal_path, 'rb') as f:
        # A Doom palette is 256 colors * 3 bytes (RGB) = 768 bytes
        return list(f.read(768))

def decode_doom_graphic(data, palette):
    width, height, _, _ = struct.unpack('<HHhh', data[:8])
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    pixels = img.load()

    column_offsets = struct.unpack(f'<{width}I', data[8:8 + (width * 4)])

    for x in range(width):
        offset = column_offsets[x]
        while offset < len(data):
            row_start = data[offset]
            if row_start == 255:
                break
            
            pixel_count = data[offset + 1]
            for i in range(pixel_count):
                if offset + 3 + i < len(data):
                    palette_idx = data[offset + 3 + i]
                    # Map index to RGB using the PLAYPAL data
                    r = palette[palette_idx * 3]
                    g = palette[palette_idx * 3 + 1]
                    b = palette[palette_idx * 3 + 2]
                    
                    if row_start + i < height:
                        pixels[x, row_start + i] = (r, g, b, 255)
            
            offset += pixel_count + 4
    return img

def main():
    palette_file = 'PLAYPAL.pal' # Ensure this is in the same folder
    if not os.path.exists(palette_file):
        print(f"Error: {palette_file} not found!")
        return

    palette = load_palette(palette_file)
    if not os.path.exists('output'):
        os.makedirs('output')

    for filename in os.listdir('.'):
        if filename.upper().startswith("STFST") and filename.lower().endswith(".lmp"):
            try:
                with open(filename, 'rb') as f:
                    img = decode_doom_graphic(f.read(), palette)
                    index = filename.upper().replace('STFST', '').replace('.LMP', '')
                    output_name = f"face_index_{index}.png"
                    img.save(os.path.join('output', output_name))
                    print(f"Converted: {output_name}")
            except Exception as e:
                print(f"Failed {filename}: {e}")

if __name__ == "__main__":
    main()