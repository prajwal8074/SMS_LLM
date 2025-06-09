import streamlit as st
import os
import io
from transformers import M2M100Tokenizer, M2M100ForConditionalGeneration
import time
import json
from typing import List
import torch
import random
import logging

if torch.cuda.is_available():
    device = torch.device("cuda:0")
else:
    device = torch.device("cpu")
    logging.warning("GPU not found, using CPU, translation will be very slow.")

st.cache(suppress_st_warning=True, allow_output_mutation=True)
st.set_page_config(page_title="M2M100 Translator")

lang_id = {
    "Afrikaans": "af",
    "Amharic": "am",
    "Arabic": "ar",
    "Asturian": "ast",
    "Azerbaijani": "az",
    "Bashkir": "ba",
    "Belarusian": "be",
    "Bulgarian": "bg",
    "Bengali": "bn",
    "Breton": "br",
    "Bosnian": "bs",
    "Catalan": "ca",
    "Cebuano": "ceb",
    "Czech": "cs",
    "Welsh": "cy",
    "Danish": "da",
    "German": "de",
    "Greeek": "el",
    "English": "en",
    "Spanish": "es",
    "Estonian": "et",
    "Persian": "fa",
    "Fulah": "ff",
    "Finnish": "fi",
    "French": "fr",
    "Western Frisian": "fy",
    "Irish": "ga",
    "Gaelic": "gd",
    "Galician": "gl",
    "Gujarati": "gu",
    "Hausa": "ha",
    "Hebrew": "he",
    "Hindi": "hi",
    "Croatian": "hr",
    "Haitian": "ht",
    "Hungarian": "hu",
    "Armenian": "hy",
    "Indonesian": "id",
    "Igbo": "ig",
    "Iloko": "ilo",
    "Icelandic": "is",
    "Italian": "it",
    "Japanese": "ja",
    "Javanese": "jv",
    "Georgian": "ka",
    "Kazakh": "kk",
    "Central Khmer": "km",
    "Kannada": "kn",
    "Korean": "ko",
    "Luxembourgish": "lb",
    "Ganda": "lg",
    "Lingala": "ln",
    "Lao": "lo",
    "Lithuanian": "lt",
    "Latvian": "lv",
    "Malagasy": "mg",
    "Macedonian": "mk",
    "Malayalam": "ml",
    "Mongolian": "mn",
    "Marathi": "mr",
    "Malay": "ms",
    "Burmese": "my",
    "Nepali": "ne",
    "Dutch": "nl",
    "Norwegian": "no",
    "Northern Sotho": "ns",
    "Occitan": "oc",
    "Oriya": "or",
    "Panjabi": "pa",
    "Polish": "pl",
    "Pushto": "ps",
    "Portuguese": "pt",
    "Romanian": "ro",
    "Russian": "ru",
    "Sindhi": "sd",
    "Sinhala": "si",
    "Slovak": "sk",
    "Slovenian": "sl",
    "Somali": "so",
    "Albanian": "sq",
    "Serbian": "sr",
    "Swati": "ss",
    "Sundanese": "su",
    "Swedish": "sv",
    "Swahili": "sw",
    "Tamil": "ta",
    "Thai": "th",
    "Tagalog": "tl",
    "Tswana": "tn",
    "Turkish": "tr",
    "Ukrainian": "uk",
    "Urdu": "ur",
    "Uzbek": "uz",
    "Vietnamese": "vi",
    "Wolof": "wo",
    "Xhosa": "xh",
    "Yiddish": "yi",
    "Yoruba": "yo",
    "Chinese": "zh",
    "Zulu": "zu",
}


@st.cache(suppress_st_warning=True, allow_output_mutation=True)
def load_model(
    pretrained_model: str = "facebook/m2m100_1.2B",
    cache_dir: str = "models/",
):
    tokenizer = M2M100Tokenizer.from_pretrained(pretrained_model, cache_dir=cache_dir)
    model = M2M100ForConditionalGeneration.from_pretrained(
        pretrained_model, cache_dir=cache_dir
    ).to(device)
    model.eval()
    return tokenizer, model


st.title("M2M100 Translator")
st.write("M2M100 is a multilingual encoder-decoder (seq-to-seq) model trained for Many-to-Many multilingual translation. It was introduced in this paper https://arxiv.org/abs/2010.11125 and first released in https://github.com/pytorch/fairseq/tree/master/examples/m2m_100 repository. The model that can directly translate between the 9,900 directions of 100 languages.\n")

st.write(" This demo uses the facebook/m2m100_1.2B model. For local inference see https://github.com/ikergarcia1996/Easy-Translate")


user_input: str = st.text_area(
    "Input text",
    height=200,
    max_chars=5120,
)

source_lang = st.selectbox(label="Source language", options=list(lang_id.keys()))
target_lang = st.selectbox(label="Target language", options=list(lang_id.keys()))

if st.button("Run"):
    time_start = time.time()
    tokenizer, model = load_model()

    src_lang = lang_id[source_lang]
    trg_lang = lang_id[target_lang]
    tokenizer.src_lang = src_lang
    with torch.no_grad():
        encoded_input = tokenizer(user_input, return_tensors="pt").to(device)
        generated_tokens = model.generate(
            **encoded_input, forced_bos_token_id=tokenizer.get_lang_id(trg_lang)
        )
        translated_text = tokenizer.batch_decode(
            generated_tokens, skip_special_tokens=True
        )[0]

    time_end = time.time()
    st.success(translated_text)

    st.write(f"Computation time: {round((time_end-time_start),3)} segs")
