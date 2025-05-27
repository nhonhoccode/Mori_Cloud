from deep_translator import GoogleTranslator

def translate_text(text, to_lang='en'):
    """
    Dịch văn bản sang ngôn ngữ đích.
    
    :param text: Chuỗi văn bản cần dịch
    :param to_lang: Ngôn ngữ đích (mặc định là 'en' - Tiếng Anh)
    :return: Văn bản đã dịch
    """
    try:
        translated = GoogleTranslator(source='auto', target=to_lang).translate(text)
        return translated
    except Exception as e:
        print(f"❌ Lỗi khi dịch văn bản: {e}")
        return text 


