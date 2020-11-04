from googletrans import Translator
from time import sleep

translator = Translator()
in_text = "как дела как дела"
in_lang = "ru"
out_lang = "en"
for i in range(15):
    result = translator.translate(in_text, src=in_lang, dest=out_lang)
    print(result.text)
    sleep(.3)