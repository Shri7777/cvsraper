import os
import zipfile
import re
import pandas as pd
import textract
from django.http import HttpResponse
from django.shortcuts import render, redirect
from pdfminer.high_level import extract_text
from .forms import CVForm
from .models import CV

# Extract email and phone numbers from text
def extract_email_and_phone(text):
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    phone_pattern = r'\+?\d[\d -]{8,12}\d'

    emails = re.findall(email_pattern, text)
    phones = re.findall(phone_pattern, text)

    return emails, phones


# View to upload PDF, DOCX, or ZIP files
def upload_file(request):
    if request.method == 'POST':
        form = CVForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()  # Save the uploaded file
            return redirect('process_files')  # Redirect to processing view
    else:
        form = CVForm()

    return render(request, 'upload.html', {'form': form})


# Process uploaded files
def process_files(request):
    cvs = CV.objects.all()  # Get all uploaded files
    data = []

    for cv in cvs:
        file_path = cv.file.path
        text = ""

        # Handle ZIP files
        if file_path.endswith('.zip'):
            extract_path = '/tmp/cv_zip_extract/'  # Directory to extract ZIP files
            if not os.path.exists(extract_path):
                os.makedirs(extract_path)

            # Extract ZIP files
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)

            # Process extracted files
            for root, _, files in os.walk(extract_path):
                for filename in files:
                    extracted_path = os.path.join(root, filename)
                    text = extract_text_from_file(extracted_path)

                    emails, phones = extract_email_and_phone(text)

                    data.append({
                        'filename': filename,
                        'emails': ', '.join(emails),
                        'phones': ', '.join(phones),
                        'text': text
                    })
        else:
            # Handle individual PDF and DOCX files
            text = extract_text_from_file(file_path)

            emails, phones = extract_email_and_phone(text)

            data.append({
                'filename': os.path.basename(file_path),
                'emails': ', '.join(emails),
                'phones': ', '.join(phones),
                'text': text
            })

    # Store extracted data in session for later use
    request.session['cv_data'] = data

    return render(request, 'results.html', {'data': data})


# Extract text from a given file based on its extension
def extract_text_from_file(file_path):
    text = ""

    if file_path.endswith('.pdf'):
        text = extract_text(file_path)  # Extract text from PDF
    elif file_path.endswith('.docx'):
        text = textract.process(file_path).decode('utf-8')  # Extract text from DOCX

    return text


# View to download Excel containing extracted information
def download_excel(request):
    # Get data from session
    data = request.session.get('cv_data', [])

    df = pd.DataFrame(data)
    excel_path = '/tmp/cv_data.xlsx'  # Path to save the Excel file

    df.to_excel(excel_path, index=False)

    # Serve the Excel file for download
    with open(excel_path, 'rb') as f:
        response = HttpResponse(f, content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="cv_data.xlsx"'
        return response
