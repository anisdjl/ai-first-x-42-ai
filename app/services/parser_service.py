import io
import base64
from typing import Tuple, Optional
from pypdf import PdfReader
from PIL import Image

def parse_file_content(filename: str, file_bytes: bytes) -> Tuple[str, Optional[str], str]:
    """
    Parse le fichier selon son type.
    Retourne :
      - text_content (str si texte/pdf/md)
      - image_base64 (str si image scannée)
      - file_type ('text' ou 'image')
    """
    ext = filename.lower().split('.')[-1]
    
    if ext in ['png', 'jpg', 'jpeg', 'webp']:
        # Traitement CV Scanné (Vision)
        b64_str = base64.b64encode(file_bytes).decode('utf-8')
        return "", b64_str, "image"
        
    elif ext == 'pdf':
        # Extraction texte PDF local
        reader = PdfReader(io.BytesIO(file_bytes))
        extracted_text = ""
        for page in reader.pages:
            extracted_text += (page.extract_text() or "") + "\n"
        
        # Si le PDF est un scan pur sans texte extrait, on peut le traiter comme image
        if len(extracted_text.strip()) < 50:
            # Fallback scan PDF si besoin
            pass
        return extracted_text, None, "text"
        
    else:
        # Markdown ou texte brut
        text = file_bytes.decode('utf-8', errors='ignore')
        return text, None, "text"
