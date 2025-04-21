import streamlit as st
import datetime
import fitz  # PyMuPDF
from pymongo import MongoClient
from bson import ObjectId
import gridfs
import logging

# Set page configuration
st.set_page_config(layout="wide")

# Configure logging
logging.basicConfig(
    filename="app_debug.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# MongoDB Connection with GridFS
@st.cache_resource
def get_mongo_connection():
    try:
        client = MongoClient("mongodb://localhost:27017/")
        db = client["logbook_database"]
        fs = gridfs.GridFS(db)
        collection = db["logbook_entries"]
        return client, db, fs, collection
    except Exception as e:
        logging.error(f"Failed to connect to MongoDB: {str(e)}")
        raise

client, db, fs, collection = get_mongo_connection()

# PDF Viewer with GridFS support
class PDFViewer:
    def __init__(self, pdf_data):
        self.pdf_document = fitz.open(stream=pdf_data, filetype="pdf")
        self.zoom_levels = [0.5, 1.0, 1.5, 2.0, 3.0]
        self.current_zoom = 1.0

    def render_page(self, page_number, zoom_level):
        page = self.pdf_document[page_number]
        mat = fitz.Matrix(zoom_level, zoom_level)
        pix = page.get_pixmap(matrix=mat)
        return pix.tobytes("png")

    def get_page_count(self):
        return len(self.pdf_document)

# Store PDF in GridFS
def store_pdf_in_gridfs(pdf_data, filename):
    try:
        file_id = fs.put(pdf_data, filename=filename)
        logging.info(f"Successfully stored PDF in GridFS with ID: {file_id}")
        return file_id
    except Exception as e:
        logging.error(f"Failed to store PDF in GridFS: {str(e)}")
        raise

# Retrieve PDF from GridFS
def get_pdf_from_gridfs(file_id):
    try:
        pdf_data = fs.get(ObjectId(file_id)).read()
        logging.info(f"Successfully retrieved PDF from GridFS with ID: {file_id}")
        return pdf_data
    except Exception as e:
        logging.error(f"Failed to retrieve PDF from GridFS: {str(e)}")
        raise

# Standardize dates in the document
def standardize_dates(document):
    for week in document["weeks"]:
        if isinstance(week["start_date"], datetime.date):
            week["start_date"] = week["start_date"].strftime('%Y-%m-%d')
        if isinstance(week["end_date"], datetime.date):
            week["end_date"] = week["end_date"].strftime('%Y-%m-%d')
        for day in week["days"].values():
            if isinstance(day["date"], datetime.date):
                day["date"] = day["date"].strftime('%Y-%m-%d')

# Prepare the document for saving
def prepare_document_for_save(document_data):
    # Standardize dates
    standardize_dates(document_data)
    # Validate structure
        
    def validate_document_structure(document_data):
        """
        Validates the structure of the document data.
        Ensures required fields are present and properly formatted.
        """
        required_fields = ["id", "pdf_file_id", "timeframe", "total_pages", "weeks"]
        for field in required_fields:
            if field not in document_data:
                raise ValueError(f"Missing required field: {field}")
        if not isinstance(document_data["weeks"], list):
            raise ValueError("The 'weeks' field must be a list.")
    validate_document_structure(document_data)
    return document_data

# Calculate week dates
def calculate_week_dates(start_date, end_date, total_pages):
    weeks_data = []
    current_date = start_date
    for page in range(total_pages):
        week_end = min(current_date + datetime.timedelta(days=4), end_date)
        weeks_data.append({
            "week_number": page + 1,
            "start_date": current_date,
            "end_date": week_end,
            "weekly_goal": "",
            "days": {
                day: {
                    "date": (current_date + datetime.timedelta(days=i)).strftime('%Y-%m-%d'),
                    "text": "",
                    "tags": []
                }
                for i, day in enumerate(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
            }
        })
        current_date = week_end + datetime.timedelta(days=3)  # Skip weekend
        if current_date > end_date:
            break
    return weeks_data

# Main Application
def main():
    st.title("Logbuch-Texteditor mit PDF-Viewer")

    # Datei-Upload
    uploaded_pdf = st.sidebar.file_uploader("PDF-Logbuch hochladen", type=["pdf"])

    if uploaded_pdf:
        try:
            # Überprüfen, ob die PDF bereits in der Datenbank existiert
            existing_entry = collection.find_one({"id": uploaded_pdf.name})
            if existing_entry:
                st.warning(f"Die PDF '{uploaded_pdf.name}' ist bereits in der Datenbank.")
            else:
                # PDF in GridFS speichern
                pdf_data = uploaded_pdf.read()
                file_id = store_pdf_in_gridfs(pdf_data, uploaded_pdf.name)

                # Einen neuen Eintrag in der Datenbank erstellen
                total_pages = PDFViewer(pdf_data).get_page_count()
                start_date = st.sidebar.date_input("Startdatum", datetime.date.today())
                end_date = st.sidebar.date_input("Enddatum", datetime.date.today() + datetime.timedelta(days=total_pages * 7))
                weeks_data = calculate_week_dates(start_date, end_date, total_pages)

                new_entry = {
                    "id": uploaded_pdf.name,
                    "pdf_file_id": str(file_id),
                    "timeframe": {"start_date": start_date.strftime('%Y-%m-%d'), "end_date": end_date.strftime('%Y-%m-%d')},
                    "total_pages": total_pages,
                    "weeks": weeks_data,
                }
                # Daten vor dem Speichern standardisieren
                standardize_dates(new_entry)

                # Den neuen Eintrag in die Datenbank einfügen
                collection.insert_one(new_entry)
                st.success(f"Die PDF '{uploaded_pdf.name}' wurde erfolgreich hochgeladen und gespeichert!")

                # Die Liste der vorhandenen Einträge aktualisieren
                existing_entries = list(collection.find({}, {"_id": 1, "id": 1}))
        except Exception as e:
            st.error(f"Fehler beim Hochladen der PDF: {str(e)}")
            logging.error(f"Fehler beim Hochladen der PDF: {str(e)}")
            
    # Vorhandene Einträge durchsuchen und bearbeiten
    st.sidebar.subheader("Vorhandene Einträge durchsuchen")
    existing_entries = list(collection.find({}, {"_id": 1, "id": 1}))  # Sicherstellen, dass die Liste aktualisiert wird
    entry_options = {str(entry["_id"]): entry.get("id", "Unbenannter Eintrag") for entry in existing_entries}
    selected_entry_id = st.sidebar.selectbox("Einen Eintrag auswählen", options=[""] + list(entry_options.keys()), format_func=lambda x: entry_options.get(x, "Einen Eintrag auswählen"))

    if selected_entry_id:
        try:
            # Den ausgewählten Eintrag abrufen
            selected_entry = collection.find_one({"_id": ObjectId(selected_entry_id)})
            pdf_data = get_pdf_from_gridfs(selected_entry["pdf_file_id"])
            pdf_viewer = PDFViewer(pdf_data)

            # PDF-Viewer anzeigen
            st.subheader(f"Eintrag anzeigen: {selected_entry.get('id', 'Unbenannter Eintrag')}")
            col1, col2 = st.columns([2, 3])

            with col1:
                st.sidebar.subheader("PDF-Viewer-Steuerung")
                zoom_level = st.sidebar.select_slider(
                    "Zoomstufe",
                    options=pdf_viewer.zoom_levels,
                    value=1.0
                )
                page_number = st.sidebar.number_input("Seite/Woche", min_value=1, max_value=selected_entry["total_pages"], value=1) - 1
                st.image(pdf_viewer.render_page(page_number, zoom_level), caption=f"Woche {page_number + 1}", use_container_width=True)

            with col2:
                # Wochen-Editor
                weeks_data = selected_entry["weeks"]
                current_week = weeks_data[page_number]
                st.subheader(f"Woche {page_number + 1} Editor")

                # Wöchentliches Ziel
                if 'weekly_goal' not in st.session_state:
                    st.session_state['weekly_goal'] = current_week["weekly_goal"]
                st.session_state['weekly_goal'] = st.text_area(
                    "Wöchentliches Ziel",
                    value=st.session_state['weekly_goal'],
                    key=f"weekly_goal_{page_number}"
                )

                # Buttons für das wöchentliche Ziel
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("NAME zum wöchentlichen Ziel hinzufügen", key=f"name_goal_{page_number}"):
                        st.session_state['weekly_goal'] += " [NAME]"
                with col2:
                    if st.button("NICHT LESBAR zum wöchentlichen Ziel hinzufügen", key=f"nl_goal_{page_number}"):
                        st.session_state['weekly_goal'] += " [NICHT LESBAR]"
                with col3:
                    if st.button("KEIN EINTRAG zum wöchentlichen Ziel hinzufügen", key=f"kein_eintrag_goal_{page_number}"):
                        st.session_state['weekly_goal'] += " [KEIN EINTRAG]"

                # Tägliche Einträge
                for day, day_data in current_week["days"].items():
                    st.write(f"**{day}** ({day_data['date']})")
                    text_key = f"text_{page_number}_{day}"
                    day_data["text"] = st.text_area(
                        f"Eintrag für {day}",
                        value=day_data["text"],
                        key=text_key
                    )

                    # Buttons für tägliche Einträge
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button(f"NAME hinzufügen", key=f"name_{text_key}"):
                            day_data["text"] += " [NAME]"
                    with col2:
                        if st.button(f"NICHT LESBAR hinzufügen", key=f"nl_{text_key}"):
                            day_data["text"] += " [NICHT LESBAR]"
                    with col3:
                        if st.button(f"KEIN EINTRAG hinzufügen", key=f"kein_eintrag_{text_key}"):
                            day_data["text"] += " [KEIN EINTRAG]"

                # Speichern-Button
                if st.button("Änderungen speichern"):
                    try:
                        # Den Eintrag in MongoDB aktualisieren
                        selected_entry["weeks"] = weeks_data
                        collection.update_one({"_id": ObjectId(selected_entry_id)}, {"$set": selected_entry})
                        st.success("Änderungen wurden erfolgreich gespeichert!")
                        logging.info(f"Eintrag mit ID {selected_entry_id} erfolgreich aktualisiert.")
                    except Exception as e:
                        st.error(f"Fehler beim Speichern der Änderungen: {str(e)}")
                        logging.error(f"Fehler beim Speichern der Änderungen: {str(e)}")

        except Exception as e:
            st.error(f"Fehler beim Laden des Eintrags: {str(e)}")
            logging.error(f"Fehler beim Laden des Eintrags: {str(e)}")

if __name__ == "__main__":
    main()