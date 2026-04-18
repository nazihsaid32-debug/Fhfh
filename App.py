import streamlit as st
import pandas as pd

# 1. Configuration de la page
st.set_page_config(page_title="Wind Farm Availability Tool", layout="wide")

# 2. Affichage de l'image dans la barre latérale (Sidebar)
st.sidebar.image("https://static.wixstatic.com/media/bbe160_691ccb3c43634bc586a0c7d25b4ad47b~mv2.jpg", use_container_width=True)

st.title("📊 Wind Farm Data Cleaner")
st.markdown("---")

# 3. Paramètres de modification manuelle (Sidebar)
st.sidebar.header("⚙️ Paramètres Manuels")
m_start = st.sidebar.text_input("Date Début (DD/MM/YYYY HH:MM:SS)")
m_end = st.sidebar.text_input("Date Fin (DD/MM/YYYY HH:MM:SS)")
m_resp = st.sidebar.selectbox("Responsabilité Exceptionnelle", ["EEM", "GE", "ONEE", "Autres"])

# 4. Base de données des Alarmes (Responsabilités par défaut)
base_rules = {
    'BackWind': 'EEM',
    'AnemCheck': 'WTG',
    'HiTemAux1': 'WTG',
    'ManualStop': 'WTG',
    'Corrective maintenance': 'WTG',
    'Out of Grid': 'ONEE'
}

# 5. Zone de téléchargement du fichier (Uploader)
uploaded_file = st.file_uploader("📂 Charger le fichier Excel SCADA (.xlsx)", type=["xlsx"])

if uploaded_file:
    # Lecture des données
    df = pd.read_excel(uploaded_file)
    
    # Conversion des colonnes de temps
    # Note: Assurez-vous que les colonnes s'appellent exactement comme ci-dessous dans votre Excel
    df['Start'] = pd.to_datetime(df['Start Data and Time'], dayfirst=True)
    df['End'] = pd.to_datetime(df['End Date and Time'], dayfirst=True)
    
    # Tri des données par Turbine et par Date
    df = df.sort_values(['WTG0', 'Start'])
    
    processed_rows = []

    # Logique de fusion des chevauchements (Overlaps)
    for wtg, group in df.groupby('WTG0'):
        if group.empty: continue
        
        c_s, c_e, c_a = group.iloc[0]['Start'], group.iloc[0]['End'], group.iloc[0]['Alarm text']
        
        for i in range(1, len(group)):
            row = group.iloc[i]
            if row['Start'] <= c_e:  # Cas de chevauchement
                c_e = max(c_e, row['End'])
            else:
                # Définition de la responsabilité
                resp = base_rules.get(c_a, 'WTG')
                
                # Vérification de l'intervention manuelle
                if m_start and m_end:
                    ms = pd.to_datetime(m_start, dayfirst=True)
                    me = pd.to_datetime(m_end, dayfirst=True)
                    if not (c_e <= ms or c_s >= me):
                        resp = m_resp

                processed_rows.append([wtg, c_a, c_s, c_e, resp])
                c_s, c_e, c_a = row['Start'], row['End'], row['Alarm text']
        
        # Ajouter la dernière ligne
        processed_rows.append([wtg, c_a, c_s, c_e, base_rules.get(c_a, 'WTG')])

    # Création du tableau final
    result_df = pd.DataFrame(processed_rows, columns=['WTG', 'Alarm', 'Start', 'End', 'Responsibility'])
    result_df['Duration (Min)'] = (result_df['End'] - result_df['Start']).dt.total_seconds() / 60

    st.success("✅ Traitement terminé avec succès ! Les chevauchements ont été supprimés.")
    
    # Affichage du tableau dans l'application
    st.dataframe(result_df)

    # 6. Bouton de téléchargement du rapport final
    output_filename = "Rapport_Final_Nettoye.xlsx"
    result_df.to_excel(output_filename, index=False)
    
    with open(output_filename, "rb") as f:
        st.download_button(
            label="📥 Télécharger le fichier Excel nettoyé",
            data=f,
            file_name=output_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
