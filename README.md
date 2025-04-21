# Logbuch Text Editor

## Overview

The **Logbuch Text Editor** is a web-based application designed to manage handwritten logbook entries. It allows users to upload PDF logbooks, store them in a MongoDB database using GridFS for PDF storage, and provides a user-friendly interface for viewing and editing entries. The application is localized in **German**, while the JSON tags used for database storage remain in **English** for consistency.

## Features

- **PDF Upload**: Upload PDF files containing handwritten logbook entries.
- **PDF Viewer**: View individual pages of the uploaded PDF with adjustable zoom levels.
- **Weekly Goals and Daily Entries**: Edit weekly goals and daily entries for each week in the logbook.
- **Database Integration**: Store metadata in MongoDB and PDFs in GridFS.
- **German Localization**: User interface is fully localized in German.

## Requirements

### Software

- Python 3.8 or higher
- MongoDB 4.4 or higher
- Required Python libraries:
  - `streamlit`
  - `pymongo`
  - `gridfs`
  - `fitz` (PyMuPDF)

### Hardware

- Minimum 4 GB RAM
- At least 10 GB of free disk space for storing PDFs in MongoDB

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/logbuch-text-editor.git
   cd logbuch-text-editor
   ```

2. **Install Required Libraries**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start MongoDB**:
   Ensure that MongoDB is running on your local machine. You can start it using:
   ```bash
   mongod
   ```

4. **Run the Application**:
   ```bash
   streamlit run latest-with-viewer.py
   ```

## Usage

### Uploading a New PDF

1. Click on **"Logbuch hochladen"** in the sidebar.
2. Select a PDF file from your computer.
3. If the PDF already exists in the database, a warning will be displayed.
4. If the PDF is new, it will be stored in GridFS, and metadata will be saved in the database.

### Viewing and Editing an Existing Entry

1. Click on **"Einträge durchsuchen"** in the sidebar.
2. Select an entry from the dropdown menu.
3. The selected entry's PDF will be displayed in the PDF viewer.
4. Use the editor to edit weekly goals and daily entries.

### Saving Changes

1. After making changes to the weekly goal or daily entries, click **"Änderungen speichern"**.
2. The program will update the entry in the database and display a success message.

## Error Handling

- **MongoDB Connection Error**: If the program cannot connect to MongoDB, an error message will be displayed. Ensure MongoDB is running.
- **Duplicate PDF Upload**: If a PDF with the same name already exists, a warning will be shown.
- **Invalid File Format**: Only PDF files are supported.

## Future Enhancements

- **OCR Integration**: Implement OCR capabilities to extract text from handwritten PDFs.
- **Advanced Search**: Add functionality to search entries by keywords or tags.
- **User Authentication**: Implement user authentication for secure access.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.
