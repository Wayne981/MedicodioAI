#!/usr/bin/env python3
"""
Clinical Information Extraction from Medical Reports
Uses traditional NLP/ML/NER methods to extract structured data from medical PDFs
"""

import json
import re
import spacy
import pandas as pd
from typing import List, Dict, Any
from dataclasses import dataclass
from collections import defaultdict
import PyPDF2
from pathlib import Path

# Try to load the medical model, fallback to en_core_web_sm if not available
try:
    nlp = spacy.load("en_core_sci_sm")  # ScispaCy model for medical text
except OSError:
    try:
        nlp = spacy.load("en_core_web_sm")
        print("Warning: Using general English model. Install en_core_sci_sm for better medical NER")
    except OSError:
        print("Error: No spaCy model found. Please install with: python -m spacy download en_core_web_sm")
        nlp = None

@dataclass
class ClinicalReport:
    """Structure to hold extracted clinical information"""
    report_id: str
    clinical_terms: List[str]
    anatomical_locations: List[str]
    diagnosis: List[str]
    procedures: List[str]
    icd_10: List[str]
    cpt: List[str]
    hcpcs: List[str]
    modifiers: List[str]

class ClinicalExtractor:
    """Main class for extracting clinical information from medical reports"""
    
    def __init__(self):
        self.nlp = nlp
        self._load_medical_dictionaries()
        self._compile_patterns()
    
    def _load_medical_dictionaries(self):
        """Load medical terminology dictionaries for enhanced recognition"""
        
        # Common medical terms and conditions
        self.medical_terms = {
            'gastrointestinal': [
                'diverticulosis', 'diverticulitis', 'hemorrhoids', 'polyp', 'polyps',
                'colitis', 'proctitis', 'gastritis', 'esophagitis', 'duodenitis',
                'bleeding', 'ulcer', 'ulceration', 'inflammation', 'stricture',
                'obstruction', 'perforation', 'fissure', 'fistula', 'abscess',
                "barrett's esophagus", 'reflux', 'gerd', 'ibd', "crohn's disease",
                'ulcerative colitis', 'celiac disease', 'gastroenteritis'
            ],
            'procedures': [
                'colonoscopy', 'endoscopy', 'egd', 'sigmoidoscopy', 'biopsy',
                'polypectomy', 'cauterization', 'ablation', 'dilation',
                'sclerotherapy', 'injection', 'clipping', 'argon plasma coagulation',
                'band ligation', 'thermal therapy', 'cryotherapy'
            ],
            'symptoms': [
                'bleeding', 'pain', 'cramping', 'nausea', 'vomiting', 'diarrhea',
                'constipation', 'bloating', 'distension', 'melena', 'hematochezia',
                'hematemesis', 'dysphagia', 'odynophagia', 'heartburn', 'reflux',
                'indigestion', 'anorexia', 'weight loss', 'fatigue', 'weakness'
            ]
        }
        
        # Anatomical locations
        self.anatomical_locations = [
            'esophagus', 'stomach', 'duodenum', 'jejunum', 'ileum', 'cecum',
            'ascending colon', 'transverse colon', 'descending colon', 'sigmoid colon',
            'rectum', 'anus', 'anal canal', 'gastroesophageal junction', 'pylorus',
            'antrum', 'fundus', 'cardia', 'terminal ileum', 'ileocecal valve',
            'appendix', 'liver', 'gallbladder', 'pancreas', 'spleen', 'peritoneum',
            'mucosa', 'submucosa', 'muscularis', 'serosa', 'lumen', 'wall'
        ]
    
    def _compile_patterns(self):
        """Compile regex patterns for code extraction"""
        
        # ICD-10 pattern: Letter + 2 digits + optional dot + optional 1-2 digits/letters
        self.icd10_pattern = re.compile(r'\b[A-Z]\d{2}(?:\.\d{1,2}[A-Z]?)?\b')
        
        # CPT pattern: 5 digits, potentially with modifiers
        self.cpt_pattern = re.compile(r'\b\d{5}\b')
        
        # HCPCS pattern: Letter + 4 digits
        self.hcpcs_pattern = re.compile(r'\b[A-Z]\d{4}\b')
        
        # Modifier pattern: 2 digits or 2 letters
        self.modifier_pattern = re.compile(r'\b(?:modifier\s+)?([A-Z]{2}|\d{2})\b', re.IGNORECASE)
        
        # Diagnosis section patterns
        self.diagnosis_patterns = [
            re.compile(r'(?:diagnosis|impression|findings?):\s*(.*?)(?:\n\n|\nPROCEDURE|\nRECOMMENDATIONS?|\nPLAN|\Z)', re.IGNORECASE | re.DOTALL),
            re.compile(r'(?:primary|secondary|final)\s+diagnosis:\s*(.*?)(?:\n\n|\n[A-Z]+:|\Z)', re.IGNORECASE | re.DOTALL)
        ]
        
        # Procedure section patterns
        self.procedure_patterns = [
            re.compile(r'(?:procedure|procedure\s+performed):\s*(.*?)(?:\n\n|\nDIAGNOSIS|\nFINDINGS?|\nIMPRESSION|\Z)', re.IGNORECASE | re.DOTALL),
            re.compile(r'(?:endoscopic|surgical)\s+procedure:\s*(.*?)(?:\n\n|\n[A-Z]+:|\Z)', re.IGNORECASE | re.DOTALL)
        ]
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""
    
    def split_reports(self, text: str) -> List[str]:
        """Split the text into individual reports"""
        # Common patterns that separate reports
        separators = [
            r'\n\s*Report\s+\d+',
            r'\n\s*REPORT\s+\d+',
            r'\n\s*Case\s+\d+',
            r'\n\s*Patient\s+\d+',
            r'\n\s*Date:.*?\n.*?Name:',
            r'\n\s*\d+\.\s*(?:Patient|Report)',
            r'\n\s*-{3,}\s*\n',  # Multiple dashes
            r'\n\s*={3,}\s*\n'   # Multiple equals signs
        ]
        
        # Try each separator pattern
        for pattern in separators:
            reports = re.split(pattern, text, flags=re.IGNORECASE)
            if len(reports) > 1:
                # Clean up reports
                cleaned_reports = []
                for i, report in enumerate(reports):
                    if report.strip():
                        # Add back the separator info for context
                        report_id = f"Report {i+1}"
                        cleaned_reports.append(report.strip())
                return cleaned_reports
        
        # If no clear separators found, try to split by page breaks or large gaps
        reports = re.split(r'\n\s*\n\s*\n', text)
        if len(reports) >= 4:  # Expecting 4 reports
            return [report.strip() for report in reports if report.strip()]
        
        # Fallback: assume the entire text is one report or split by length
        if len(text) > 1000:
            # Simple length-based splitting for 4 reports
            length = len(text) // 4
            reports = []
            for i in range(4):
                start = i * length
                end = (i + 1) * length if i < 3 else len(text)
                reports.append(text[start:end].strip())
            return reports
        
        return [text]  # Single report
    
    def extract_medical_codes(self, text: str) -> Dict[str, List[str]]:
        """Extract ICD-10, CPT, HCPCS codes and modifiers"""
        codes = {
            'icd_10': [],
            'cpt': [],
            'hcpcs': [],
            'modifiers': []
        }
        
        # Extract ICD-10 codes
        icd10_matches = self.icd10_pattern.findall(text)
        codes['icd_10'] = list(set(icd10_matches))
        
        # Extract CPT codes
        cpt_matches = self.cpt_pattern.findall(text)
        # Filter out codes that are clearly not CPT (like years, etc.)
        valid_cpt = [code for code in cpt_matches if 10000 <= int(code) <= 99999]
        codes['cpt'] = list(set(valid_cpt))
        
        # Extract HCPCS codes
        hcpcs_matches = self.hcpcs_pattern.findall(text)
        codes['hcpcs'] = list(set(hcpcs_matches))
        
        # Extract modifiers
        modifier_matches = self.modifier_pattern.findall(text)
        codes['modifiers'] = list(set(modifier_matches))
        
        return codes
    
    def extract_clinical_terms(self, text: str) -> List[str]:
        """Extract clinical terms using NER and pattern matching"""
        clinical_terms = set()
        
        # Use spaCy NER if available
        if self.nlp:
            doc = self.nlp(text.lower())
            for ent in doc.ents:
                if ent.label_ in ['DISEASE', 'SYMPTOM', 'TREATMENT', 'MEDICAL_CONDITION']:
                    clinical_terms.add(ent.text)
        
        # Pattern-based extraction using medical dictionaries
        text_lower = text.lower()
        
        for category, terms in self.medical_terms.items():
            for term in terms:
                if term in text_lower:
                    clinical_terms.add(term)
                    
                # Also check for partial matches and variations
                pattern = re.compile(r'\b' + re.escape(term) + r'(?:s|es|ies)?\b', re.IGNORECASE)
                matches = pattern.findall(text)
                clinical_terms.update([match.lower() for match in matches])
        
        return list(clinical_terms)
    
    def extract_anatomical_locations(self, text: str) -> List[str]:
        """Extract anatomical locations"""
        locations = set()
        text_lower = text.lower()
        
        for location in self.anatomical_locations:
            if location in text_lower:
                locations.add(location)
                
            # Check for variations and partial matches
            pattern = re.compile(r'\b' + re.escape(location) + r'(?:al|ic|ine|ar)?\b', re.IGNORECASE)
            matches = pattern.findall(text)
            if matches:
                locations.add(location)
        
        return list(locations)
    
    def extract_diagnosis(self, text: str) -> List[str]:
        """Extract diagnosis information"""
        diagnoses = []
        
        # Look for diagnosis sections
        for pattern in self.diagnosis_patterns:
            matches = pattern.findall(text)
            for match in matches:
                # Clean up the diagnosis text
                diagnosis_text = re.sub(r'\s+', ' ', match.strip())
                if diagnosis_text:
                    # Split multiple diagnoses
                    diagnosis_list = re.split(r'[;\n]|(?:\d+\.)', diagnosis_text)
                    for diag in diagnosis_list:
                        diag = diag.strip().rstrip('.')
                        if len(diag) > 5:  # Filter out very short entries
                            diagnoses.append(diag)
        
        # If no structured diagnosis found, extract from clinical terms
        if not diagnoses:
            clinical_terms = self.extract_clinical_terms(text)
            condition_terms = [term for term in clinical_terms 
                             if any(cond in term for cond in self.medical_terms.get('gastrointestinal', []))]
            diagnoses = condition_terms[:3]  # Limit to top 3
        
        return list(set(diagnoses))
    
    def extract_procedures(self, text: str) -> List[str]:
        """Extract procedure information"""
        procedures = []
        
        # Look for procedure sections
        for pattern in self.procedure_patterns:
            matches = pattern.findall(text)
            for match in matches:
                procedure_text = re.sub(r'\s+', ' ', match.strip())
                if procedure_text:
                    procedures.append(procedure_text)
        
        # Also extract known procedures from text
        text_lower = text.lower()
        for procedure in self.medical_terms.get('procedures', []):
            if procedure in text_lower:
                procedures.append(procedure)
        
        return list(set(procedures))
    
    def process_report(self, report_text: str, report_id: str) -> ClinicalReport:
        """Process a single report and extract all information"""
        
        # Extract medical codes
        codes = self.extract_medical_codes(report_text)
        
        # Extract clinical information
        clinical_terms = self.extract_clinical_terms(report_text)
        anatomical_locations = self.extract_anatomical_locations(report_text)
        diagnosis = self.extract_diagnosis(report_text)
        procedures = self.extract_procedures(report_text)
        
        return ClinicalReport(
            report_id=report_id,
            clinical_terms=clinical_terms,
            anatomical_locations=anatomical_locations,
            diagnosis=diagnosis,
            procedures=procedures,
            icd_10=codes['icd_10'],
            cpt=codes['cpt'],
            hcpcs=codes['hcpcs'],
            modifiers=codes['modifiers']
        )
    
    def process_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Process the entire PDF and return structured JSON for all reports"""
        
        # Extract text from PDF
        full_text = self.extract_text_from_pdf(pdf_path)
        if not full_text:
            print("No text extracted from PDF")
            return []
        
        # Split into individual reports
        reports = self.split_reports(full_text)
        print(f"Found {len(reports)} reports")
        
        # Process each report
        results = []
        for i, report_text in enumerate(reports):
            report_id = f"Report {i+1}"
            
            try:
                clinical_report = self.process_report(report_text, report_id)
                
                # Convert to required JSON format
                result = {
                    "ReportID": clinical_report.report_id,
                    "Clinical Terms": clinical_report.clinical_terms,
                    "Anatomical Locations": clinical_report.anatomical_locations,
                    "Diagnosis": clinical_report.diagnosis,
                    "Procedures": clinical_report.procedures,
                    "ICD-10": clinical_report.icd_10,
                    "CPT": clinical_report.cpt,
                    "HCPCS": clinical_report.hcpcs,
                    "Modifiers": clinical_report.modifiers
                }
                
                results.append(result)
                print(f"Processed {report_id}")
                
            except Exception as e:
                print(f"Error processing {report_id}: {e}")
                continue
        
        return results

def main():
    """Main function to run the clinical extraction"""
    
    extractor = ClinicalExtractor()
    
    # Look for the PDF file
    pdf_path = "Input Data for assignment.pdf"
    
    if not Path(pdf_path).exists():
        print(f"PDF file '{pdf_path}' not found in current directory.")
        print("Please ensure the PDF file is in the same directory as this script.")
        
        # Create a sample output format for demonstration
        sample_output = [
            {
                "ReportID": "Report 1",
                "Clinical Terms": ["colonoscopy", "diverticulosis", "hemorrhoids"],
                "Anatomical Locations": ["colon", "rectum", "sigmoid"],
                "Diagnosis": ["internal hemorrhoids", "diverticulosis"],
                "Procedures": ["colonoscopy", "biopsy"],
                "ICD-10": ["K57.30", "K64.1"],
                "CPT": ["45378", "45380"],
                "HCPCS": [],
                "Modifiers": []
            }
        ]
        
        print("\nSample output format:")
        print(json.dumps(sample_output, indent=2))
        return
    
    # Process the PDF
    results = extractor.process_pdf(pdf_path)
    
    # Save results to JSON file
    output_file = "clinical_extraction_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nExtraction complete! Results saved to: {output_file}")
    print(f"Processed {len(results)} reports")
    
    # Display summary
    for result in results:
        print(f"\n{result['ReportID']}:")
        print(f"  Clinical Terms: {len(result['Clinical Terms'])}")
        print(f"  Anatomical Locations: {len(result['Anatomical Locations'])}")
        print(f"  Diagnoses: {len(result['Diagnosis'])}")
        print(f"  Procedures: {len(result['Procedures'])}")
        print(f"  ICD-10 Codes: {len(result['ICD-10'])}")
        print(f"  CPT Codes: {len(result['CPT'])}")

if __name__ == "__main__":
    main() 