import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI()

def generate_game_prompt(context, user_input):
    prompt = f"""
    Tu es un Dungeon Master (DM) pour D&D.
    Contexte actuel: {context.get('history', [])}
    Le joueur dit: {user_input}.
    Réponds en décrivant clairement ce qui se passe ensuite.
    """
    return prompt.strip()

def get_gpt_response(prompt):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # <-- Change ici !
        messages=[{"role": "system", "content": prompt}],
        temperature=0.8
    )
    return response.choices[0].message.content

def generate_pixel_art(prompt):
    try:
        image_response = client.images.generate(
            prompt=prompt,
            n=1,
            size="256x256"
        )
        return image_response.data[0].url
    except Exception as e:
        print(f"Erreur de génération d'image: {e}")
        return None
