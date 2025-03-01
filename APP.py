import streamlit as st
import os
import re
import time
import tempfile
import csv 
from datetime import datetime
import google.generativeai as genai
from requests.exceptions import ConnectionError
from urllib3.exceptions import ProtocolError
from google.api_core.exceptions import TooManyRequests
from supabase import create_client, Client

# =================== Inicialización de Supabase ===================
# Se obtienen las credenciales desde st.secrets
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =================== Configuración de la API de Gemini ===================

api_keys = [
    "AIzaSyC5oc1_9Zp0xb37z2u7M1v3ov4Js1DyUSk",
    "AIzaSyAEaxnxgoMXwg9YVRmRH_tKVGD3pNgHKkk"
]

current_api_key_index = 0

def configure_api():
    global current_api_key_index
    genai.configure(api_key=api_keys[current_api_key_index])

configure_api()

generation_config = {
    "temperature": 0.4,
    "top_p": 0.8,
    "top_k": 32,
    "max_output_tokens": 50,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
]

def create_model():
    return genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        generation_config=generation_config,
        safety_settings=safety_settings
    )

model = create_model()

def switch_api_key():
    global current_api_key_index, model
    current_api_key_index = (current_api_key_index + 1) % len(api_keys)
    configure_api()
    model = create_model()

def send_prompt_to_gemini(prompt):
    try:
        response = model.generate_content([prompt])
        return response.text.strip() if response and response.text else "Sin respuesta."
    except Exception as e:
        switch_api_key()
        try:
            response = model.generate_content([prompt])
            return response.text.strip() if response and response.text else "Sin respuesta."
        except Exception as e:
            return "Error al procesar la solicitud."

# ============ Funciones para subir el video a Gemini ============
def upload_to_gemini(path, mime_type=None):
    """
    Sube el archivo dado a Gemini y retorna el objeto de archivo.
    """
    file = genai.upload_file(path, mime_type=mime_type)
    st.write(f"Archivo '{file.display_name}' subido a: {file.uri}")
    return file

def wait_for_files_active(files):
    """
    Espera a que los archivos subidos estén activos.
    Utiliza un spinner de Streamlit para mostrar el progreso.
    """
    with st.spinner("Esperando a que el archivo se procese..."):
        for i, file in enumerate(files):
            while file.state.name == "PROCESSING":
                time.sleep(10)
                file = genai.get_file(file.name)
            if file.state.name != "ACTIVE":
                raise Exception(f"El archivo {file.name} falló al procesarse")
    st.success("El archivo ya está activo.")

# ============ Función para guardar la respuesta en Supabase ============
def save_response_to_supabase(data):
    response = supabase.table("responses").insert(data).execute()
    return response

# =================== Inicio de la aplicación Streamlit ===================

# Selección del idioma al inicio
language = st.radio("Select Language / Seleccione el idioma:", options=["Español", "English"])

if language == "English":
    st.title("Preventive pet health assessment")
    st.markdown(
        """
        **Welcome!**  
        This application uses artificial intelligence to provide an initial evaluation of your pet's health.  

        **How to use this application:**  
        1. **Select your language.**  
        2. **Enter your owner information:** Country, Owner's Name, Contact Number (with country code), and Email.  
        3. **Provide general information** about your pet, including its type, eating habits, elimination, age, and grooming.  
        4. **Answer additional questions** specific to your pet type (Cat or Dog).  
        5. **Indicate if your pet has experienced diarrhea or vomiting.**  
           - If yes, a warning will appear urging you to consult a veterinarian immediately.  
        6. **Optionally, upload a video** of your pet.  
        7. Click the **Evaluate** button to receive a detailed, empathetic analysis with clear recommendations.

        **Note:** This is an initial assessment provided by an AI, which may not be entirely accurate. If in doubt, please consult a veterinarian.
        """
    )
    
    # Información del Dueño
    st.subheader("Owner Information")
    owner_country = st.text_input("Country")
    owner_name = st.text_input("Owner's Name")
    owner_contact = st.text_input("Contact Number (with country code)")
    owner_email = st.text_input("Email")
    
    # Preguntas sobre el animal
    tipo_animal = st.radio("What type of animal is it?", options=["Cat", "Dog"])
    
    # Preguntas generales
    comida = st.radio("Is the animal eating and drinking?", options=["Yes", "No"])
    eliminacion = st.radio("Is it eliminating normally?", options=["Yes", "No"])
    edad = st.number_input("How old is the animal?", min_value=0, max_value=50, value=3)
    acicala = st.radio("Is it grooming itself properly?", options=["Yes", "No"])
    
    # Pregunta sobre diarrea o vómito
    diarrhea_vomiting = st.radio("Has the animal experienced diarrhea or vomiting?", options=["Yes", "No"])
    if diarrhea_vomiting == "Yes":
        st.warning("Warning: It is highly recommended to consult a veterinarian immediately.")
    
    # Preguntas específicas según el tipo de animal
    if tipo_animal == "Cat":
        st.subheader("Additional Questions for Cats")
        grooming_regular = st.radio("Does the cat groom itself regularly?", options=["Yes", "No"])
        cambios_grooming = st.radio("Have there been any changes in its grooming habits?", options=["Yes", "No"])
        comportamiento_cambio = st.radio("Has the cat's behavior changed recently?", options=["Yes", "No"])
        sociable = st.radio("Is the cat sociable or shy?", options=["Sociable", "Shy"])
        ocultarse = st.radio("Does the cat hide or avoid interaction?", options=["Yes", "No"])
        reacio = st.radio("Does the cat seem reluctant to go out even to see its favorite person or get its food?", options=["Yes", "No"])
        
        st.write("Which of these images most closely resembles your cat's overall condition recently?")
        col1, col2 = st.columns(2)
        with col1:
            st.image("gato_normal.png", caption="Normal condition (Ears up, mouth closed, eyes open, relaxed whiskers)")
        with col2:
            st.image("gato_dolor.png", caption="Condition with pain (Eyes closed, ears down, mouth open, bristled whiskers)")
        
        imagen_estado_gato = st.radio(
            "Select the image that best represents your cat's condition:",
            options=["Normal condition", "Condition with pain"]
        )
    else:
        st.subheader("Additional Questions for Dogs")
        aseo_regular = st.radio("Does the dog clean or lick itself regularly?", options=["Yes", "No"])
        cambios_aseo = st.radio("Have there been any changes in its grooming habits?", options=["Yes", "No"])
        comportamiento_cambio = st.radio("Has the dog's behavior changed recently?", options=["Yes", "No"])
        sociable = st.radio("Is the dog sociable or does it show shyness/aggressiveness?", options=["Sociable", "Shy/Aggressive"])
        ocultarse = st.radio("Does the dog hide or avoid interaction?", options=["Yes", "No"])
        reacio = st.radio("Does the dog seem reluctant to go out even to interact with its owner or receive food?", options=["Yes", "No"])
    
    video_file = st.file_uploader("Upload a video of the pet (optional)", type=["mp4", "mov", "avi"])

else:
    st.title("Evaluación Inicial de Salud de Mascotas")
    st.markdown(
        """
        **¡Bienvenido!**  
        Esta aplicación utiliza inteligencia artificial para ofrecer una evaluación inicial de la salud de su mascota.  

        **Cómo usar esta aplicación:**  
        1. **Seleccione el idioma.**  
        2. **Ingrese la información del dueño:** País, Nombre del dueño, Número de contacto (con indicativo del país) y Email.  
        3. **Proporcione información general** sobre su mascota, incluyendo tipo, hábitos alimenticios, eliminación, edad y acicalamiento.  
        4. **Responda las preguntas adicionales** específicas según el tipo de animal (Gato o Perro).  
        5. **Indique si el animal ha tenido diarrea o vómito.**  
           - Si responde que sí, se mostrará una advertencia para que consulte a un veterinario de inmediato.  
        6. **Opcionalmente, suba un video** de su mascota.  
        7. Presione el botón **Evaluar** para recibir un análisis detallado y empático del estado de su mascota con recomendaciones claras.

        **Nota:** Esta es una evaluación inicial proporcionada por una IA, la cual puede no ser completamente precisa. Ante cualquier duda, consulte a un veterinario.
        """
    )
    
    # Información del Dueño
    st.subheader("Información del Dueño")
    owner_country = st.text_input("País")
    owner_name = st.text_input("Nombre del dueño")
    owner_contact = st.text_input("Número de contacto (con indicativo del país)")
    owner_email = st.text_input("Email")
    
    # Preguntas sobre el animal
    tipo_animal = st.radio("¿Qué tipo de animal es?", options=["Gato", "Perro"])
    
    # Preguntas generales
    comida = st.radio("¿Está comiendo y tomando agua?", options=["Sí", "No"])
    eliminacion = st.radio("¿Está orinando y defecando normalmente?", options=["Sí", "No"])
    edad = st.number_input("¿Qué edad tiene el animal?", min_value=0, max_value=50, value=3)
    acicala = st.radio("¿Se acicala correctamente?", options=["Sí", "No"])
    
    # Pregunta sobre diarrea o vómito
    diarrhea_vomiting = st.radio("¿El animal ha tenido diarrea o vómito?", options=["Sí", "No"])
    if diarrhea_vomiting == "Sí":
        st.warning("Advertencia: Es altamente recomendable consultar a un veterinario inmediatamente.")
    
    # Preguntas específicas según el tipo de animal
    if tipo_animal == "Gato":
        st.subheader("Preguntas adicionales para gatos")
        grooming_regular = st.radio("¿El gato se acicala regularmente?", options=["Sí", "No"])
        cambios_grooming = st.radio("¿Ha habido algún cambio en sus hábitos de acicalamiento?", options=["Sí", "No"])
        comportamiento_cambio = st.radio("¿Ha cambiado recientemente el comportamiento del gato?", options=["Sí", "No"])
        sociable = st.radio("¿El gato es sociable o tímido?", options=["Sociable", "Tímido"])
        ocultarse = st.radio("¿El gato se esconde o evita interactuar?", options=["Sí", "No"])
        reacio = st.radio("¿El gato se muestra reacio a salir incluso para ver a su persona favorita o recibir su comida?", options=["Sí", "No"])
        
        st.write("¿Cuál de estas imágenes se parece más al estado general de su gato en el último tiempo?")
        col1, col2 = st.columns(2)
        with col1:
            st.image("gato_normal.png", caption="Estado normal (Orejas arriba, boca cerrada, ojos abiertos, Bigotes relajados)")
        with col2:
            st.image("gato_dolor.png", caption="Estado con dolor (Ojos cerrados, orejas caídas, boca abierta, Bigotes erizados)")
        
        imagen_estado_gato = st.radio(
            "Seleccione la imagen que más se parezca al estado de su gato:",
            options=["Estado normal", "Estado con dolor"]
        )
    else:
        st.subheader("Preguntas adicionales para perros")
        aseo_regular = st.radio("¿El perro se limpia o se lame regularmente?", options=["Sí", "No"])
        cambios_aseo = st.radio("¿Ha habido algún cambio en sus hábitos de aseo?", options=["Sí", "No"])
        comportamiento_cambio = st.radio("¿Ha cambiado recientemente el comportamiento del perro?", options=["Sí", "No"])
        sociable = st.radio("¿El perro es sociable o muestra timidez/agresividad?", options=["Sí", "No"])
        ocultarse = st.radio("¿El perro se esconde o evita interactuar?", options=["Sí", "No"])
        reacio = st.radio("¿El perro se muestra reacio a salir incluso para interactuar con su dueño o recibir su comida?", options=["Sí", "No"])
    
    video_file = st.file_uploader("Sube un video del animal (opcional)", type=["mp4", "mov", "avi"])

video_uri = None
if video_file is not None:
    # Guardar el archivo subido en un archivo temporal
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
        temp_file.write(video_file.getvalue())
        temp_file_path = temp_file.name
    st.write(f"Video guardado temporalmente en: {temp_file_path}")
    
    # Subir el video a Gemini y esperar a que esté activo
    try:
        uploaded_video = upload_to_gemini(temp_file_path, mime_type="video/mp4")
        wait_for_files_active([uploaded_video])
        video_uri = uploaded_video.uri
    except Exception as e:
        st.error(f"Error al subir o procesar el video: {e}")

# Botón para evaluar / Evaluate button
button_text = "Evaluate" if language == "English" else "Evaluar"
if st.button(button_text):
    if language == "English":
        prompt = f"Pet Health Evaluation for a {tipo_animal}.\n"
        prompt += f"- Eating and drinking: {comida}\n"
        prompt += f"- Normal elimination: {eliminacion}\n"
        prompt += f"- Age: {edad}\n"
        prompt += f"- Grooming: {acicala}\n\n"
        prompt += "Owner Information:\n"
        prompt += f"- Country: {owner_country}\n"
        prompt += f"- Owner's Name: {owner_name}\n"
        prompt += f"- Contact Number: {owner_contact}\n"
        prompt += f"- Email: {owner_email}\n\n"
        
        if tipo_animal == "Cat":
            prompt += "Additional questions for cats:\n"
            prompt += f"- Regular grooming: {grooming_regular}\n"
            prompt += f"- Changes in grooming: {cambios_grooming}\n"
            prompt += f"- Change in behavior: {comportamiento_cambio}\n"
            prompt += f"- Sociability: {sociable}\n"
            prompt += f"- Hiding: {ocultarse}\n"
            prompt += f"- Reluctance to go out: {reacio}\n"
            prompt += f"- Image representing overall condition: {imagen_estado_gato}\n\n"
        else:
            prompt += "Additional questions for dogs:\n"
            prompt += f"- Regular cleaning/licking: {aseo_regular}\n"
            prompt += f"- Changes in grooming habits: {cambios_aseo}\n"
            prompt += f"- Change in behavior: {comportamiento_cambio}\n"
            prompt += f"- Sociability: {sociable}\n"
            prompt += f"- Hiding: {ocultarse}\n"
            prompt += f"- Reluctance to go out: {reacio}\n\n"
        
        prompt += f"- Diarrhea or vomiting: {diarrhea_vomiting}\n\n"
        
        prompt += "Evaluation criteria:\n"
        prompt += "Eyes: Are the eyes half-closed or narrowed? Is there any wrinkling around the eyes?\n"
        prompt += "Nose and Cheeks: Is the bridge of the nose flattened or elongated? Are the cheeks flattened or appear sunken?\n"
        prompt += "Ears: Are the ears turned inward and forward, creating a pointed shape? Has the space between the ears increased?\n"
        prompt += "Whiskers: Are the whiskers stiff and held close to the face? Are the whiskers clumped together? Have the whiskers lost their natural downward curve?\n"
        prompt += "Additional Considerations: Pain Assessment using a validated scale (e.g., Feline Grimace Scale for cats) and species-specific features.\n\n"
        
        if video_uri:
            prompt += f"Uploaded video: {video_uri}\n\n"
        
        prompt += ("Please analyze all the provided information accurately, but respond in a kind and approachable manner. "
                   "Explain what is observed and provide clear recommendations on actions to take, using an empathetic and understanding tone. "
                   "The response should be detailed and deep, without losing precision in the analysis.\n")
        
        prompt += "\n**Note:** This information is analyzed by an AI, which may be incorrect. In case of any doubt, please consult a veterinarian."
    else:
        prompt = f"Evaluación de salud para un {tipo_animal}.\n"
        prompt += f"- Comiendo y bebiendo: {comida}\n"
        prompt += f"- Eliminación normal: {eliminacion}\n"
        prompt += f"- Edad: {edad}\n"
        prompt += f"- Acicalamiento: {acicala}\n\n"
        prompt += "Información del Dueño:\n"
        prompt += f"- País: {owner_country}\n"
        prompt += f"- Nombre del dueño: {owner_name}\n"
        prompt += f"- Número de contacto: {owner_contact}\n"
        prompt += f"- Email: {owner_email}\n\n"
        
        if tipo_animal == "Gato":
            prompt += "Preguntas específicas para gatos:\n"
            prompt += f"- Se acicala regularmente: {grooming_regular}\n"
            prompt += f"- Cambios en el acicalamiento: {cambios_grooming}\n"
            prompt += f"- Cambio en comportamiento: {comportamiento_cambio}\n"
            prompt += f"- Sociabilidad: {sociable}\n"
            prompt += f"- Se esconde: {ocultarse}\n"
            prompt += f"- Reacio a salir: {reacio}\n"
            prompt += f"- Imagen que representa el estado general: {imagen_estado_gato}\n\n"
        else:
            prompt += "Preguntas específicas para perros:\n"
            prompt += f"- Se limpia o lame regularmente: {aseo_regular}\n"
            prompt += f"- Cambios en hábitos de aseo: {cambios_aseo}\n"
            prompt += f"- Cambio en comportamiento: {comportamiento_cambio}\n"
            prompt += f"- Sociabilidad: {sociable}\n"
            prompt += f"- Se esconde: {ocultarse}\n"
            prompt += f"- Reacio a salir: {reacio}\n\n"
        
        prompt += f"- Diarrea o vómito: {diarrhea_vomiting}\n\n"
        
        prompt += "Criterios para evaluar la información:\n"
        prompt += "Eyes: ¿Los ojos están entrecerrados o se ven estrechos? ¿Hay algún fruncimiento alrededor de los ojos?\n"
        prompt += "Nose and Cheeks: ¿El puente de la nariz está aplanado o alargado? ¿Las mejillas están aplanadas o se ven hundidas?\n"
        prompt += "Ears: ¿Las orejas están giradas hacia adentro y hacia adelante, creando una forma puntiaguda? ¿Ha aumentado el espacio entre las orejas?\n"
        prompt += "Whiskers: ¿Los bigotes están rígidos y pegados a la cara? ¿Los bigotes se ven aglomerados? ¿Han perdido los bigotes su curva natural hacia abajo?\n"
        prompt += "Consideraciones adicionales: Evaluación del dolor usando una escala validada (por ejemplo, Feline Grimace Scale para gatos) y características específicas de la especie.\n\n"
        
        if video_uri:
            prompt += f"Video cargado: {video_uri}\n\n"
        
        prompt += ("Por favor, analiza toda la información proporcionada de forma precisa, pero respondiendo de manera amable y cercana. "
                   "Explique lo que se observa y brinde recomendaciones claras sobre qué acciones tomar, en un tono empático y comprensivo. "
                   "La respuesta debe ser detallada y profunda, sin perder la precisión en el análisis.\n")
        
        prompt += "\n**Nota:** Esta información es analizada por una IA, la cual puede equivocarse. Ante cualquier duda, consulte a un veterinario."
    
    st.write("El siguiente prompt se enviará a Gemini:")
    st.code(prompt)
    
    # Enviar el prompt a Gemini y obtener la respuesta
    respuesta = send_prompt_to_gemini(prompt)
    if language == "English":
        st.subheader("AI Response:")
    else:
        st.subheader("Respuesta de la IA:")
    st.write(respuesta)
    
    # Recopilar los datos para guardar en la base de datos Supabase
    data = {
        "timestamp": datetime.now().isoformat(),
        "language": language,
        "owner_country": owner_country,
        "owner_name": owner_name,
        "owner_contact": owner_contact,
        "owner_email": owner_email,
        "tipo_animal": tipo_animal,
        "comida": comida,
        "eliminacion": eliminacion,
        "edad": edad,
        "acicala": acicala,
        "diarrhea_vomiting": diarrhea_vomiting,
        "video_uri": video_uri if video_uri is not None else "",
        "prompt": prompt,
        "ai_response": respuesta
    }
    # Agregar campos adicionales según el tipo de animal
    if tipo_animal in ["Cat", "Gato"]:
        data["grooming_regular"] = grooming_regular
        data["cambios_grooming"] = cambios_grooming
        data["comportamiento_cambio"] = comportamiento_cambio
        data["sociable"] = sociable
        data["ocultarse"] = ocultarse
        data["reacio"] = reacio
        data["imagen_estado"] = imagen_estado_gato
    else:
        data["aseo_regular"] = aseo_regular
        data["cambios_aseo"] = cambios_aseo
        data["comportamiento_cambio"] = comportamiento_cambio
        data["sociable"] = sociable
        data["ocultarse"] = ocultarse
        data["reacio"] = reacio

    # Guardar los datos en Supabase en lugar de un CSV
    response = save_response_to_supabase(data)
    st.write("Consulta guardada en la base de datos Supabase:", response)

