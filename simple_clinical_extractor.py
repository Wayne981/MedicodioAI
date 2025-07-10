#!/usr/bin/env python3
"""
Simplified Clinical Information Extraction System
Works with basic Python libraries to avoid dependency conflicts
"""

import json
import re
import sys
from typing import List, Dict, Any
from dataclasses import dataclass
from pathlib import Path

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    print("PyPDF2 not available - will work with text files instead")
    PDF_AVAILABLE = False

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

class SimpleClinicalExtractor:
    """Simplified clinical extractor using regex and dictionaries only"""
    
    def __init__(self):
        self._load_medical_dictionaries()
        self._compile_patterns()
    
    def _load_medical_dictionaries(self):
        """Load comprehensive medical terminology dictionaries"""
        
        # Gastrointestinal conditions and findings
        self.medical_terms = [
            'diverticulosis', 'diverticulitis', 'hemorrhoids', 'polyp', 'polyps',
            'colitis', 'proctitis', 'gastritis', 'esophagitis', 'duodenitis',
            'bleeding', 'ulcer', 'ulceration', 'inflammation', 'stricture',
            'obstruction', 'perforation', 'fissure', 'fistula', 'abscess',
            "barrett's esophagus", 'reflux', 'gerd', 'ibd', "crohn's disease",
            'ulcerative colitis', 'celiac disease', 'gastroenteritis',
            'adenoma', 'adenomatous', 'hyperplastic', 'sessile', 'pedunculated',
            'erosion', 'erythema', 'friability', 'nodular', 'villous',
            'tubular', 'serrated', 'dysplasia', 'metaplasia', 'neoplasia'
        ]
        
        # Procedures
        self.procedures = [
            'colonoscopy', 'endoscopy', 'egd', 'sigmoidoscopy', 'biopsy',
            'polypectomy', 'cauterization', 'ablation', 'dilation',
            'sclerotherapy', 'injection', 'clipping', 'argon plasma coagulation',
            'band ligation', 'thermal therapy', 'cryotherapy',
            'esophagogastroduodenoscopy', 'upper endoscopy', 'lower endoscopy',
            'endoscopic mucosal resection', 'emr', 'esd', 'hemostasis'
        ]
        
        # Symptoms
        self.symptoms = [
            'bleeding', 'pain', 'cramping', 'nausea', 'vomiting', 'diarrhea',
            'constipation', 'bloating', 'distension', 'melena', 'hematochezia',
            'hematemesis', 'dysphagia', 'odynophagia', 'heartburn', 'reflux',
            'indigestion', 'anorexia', 'weight loss', 'fatigue', 'weakness',
            'abdominal pain', 'rectal bleeding', 'change in bowel habits'
        ]
        
        # Anatomical locations
        self.anatomical_locations = [
            'esophagus', 'stomach', 'duodenum', 'jejunum', 'ileum', 'cecum',
            'ascending colon', 'transverse colon', 'descending colon', 'sigmoid colon',
            'rectum', 'anus', 'anal canal', 'gastroesophageal junction', 'pylorus',
            'antrum', 'fundus', 'cardia', 'terminal ileum', 'ileocecal valve',
            'appendix', 'liver', 'gallbladder', 'pancreas', 'spleen', 'peritoneum',
            'mucosa', 'submucosa', 'muscularis', 'serosa', 'lumen', 'wall',
            'distal', 'proximal', 'sigmoid', 'cecal', 'hepatic flexure', 'splenic flexure'
        ]
    
    def _compile_patterns(self):
        """Compile regex patterns for medical codes and sections"""
        
        # Medical code patterns
        self.icd10_pattern = re.compile(r'\b[A-Z]\d{2}(?:\.\d{1,2}[A-Z]?)?\b')
        self.cpt_pattern = re.compile(r'\b\d{5}\b')
        self.hcpcs_pattern = re.compile(r'\b[A-Z]\d{4}\b')
        self.modifier_pattern = re.compile(r'\b(?:modifier\s+)?([A-Z]{2}|\d{2})\b', re.IGNORECASE)
        
        # Section patterns
        self.diagnosis_patterns = [
            re.compile(r'(?:diagnosis|impression|findings?):\s*(.*?)(?:\n\n|\nPROCEDURE|\nRECOMMENDATIONS?|\nPLAN|\Z)', re.IGNORECASE | re.DOTALL),
            re.compile(r'(?:primary|secondary|final)\s+diagnosis:\s*(.*?)(?:\n\n|\n[A-Z]+:|\Z)', re.IGNORECASE | re.DOTALL)
        ]
        
        self.procedure_patterns = [
            re.compile(r'(?:procedure|procedure\s+performed):\s*(.*?)(?:\n\n|\nDIAGNOSIS|\nFINDINGS?|\nIMPRESSION|\Z)', re.IGNORECASE | re.DOTALL),
            re.compile(r'(?:endoscopic|surgical)\s+procedure:\s*(.*?)(?:\n\n|\n[A-Z]+:|\Z)', re.IGNORECASE | re.DOTALL)
        ]
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        if not PDF_AVAILABLE:
            return ""
        
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
        """Split text into individual reports"""
        separators = [
            r'\n\s*Report\s+\d+',
            r'\n\s*REPORT\s+\d+', 
            r'\n\s*Case\s+\d+',
            r'\n\s*Patient\s+\d+',
            r'\n\s*Date:.*?\n.*?Name:',
            r'\n\s*\d+\.\s*(?:Patient|Report)',
            r'\n\s*-{3,}\s*\n',
            r'\n\s*={3,}\s*\n'
        ]
        
        for pattern in separators:
            reports = re.split(pattern, text, flags=re.IGNORECASE)
            if len(reports) > 1:
                return [report.strip() for report in reports if report.strip()]
        
        # Fallback: split by large gaps or assume single report
        reports = re.split(r'\n\s*\n\s*\n', text)
        if len(reports) >= 4:
            return [report.strip() for report in reports if report.strip()]
        
        return [text] if text.strip() else []
    
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
        
        # Extract CPT codes (filter valid range)
        cpt_matches = self.cpt_pattern.findall(text)
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
        """Extract clinical terms using pattern matching"""
        clinical_terms = set()
        text_lower = text.lower()
        
        # Find all medical terms
        all_terms = self.medical_terms + self.symptoms
        for term in all_terms:
            if term in text_lower:
                clinical_terms.add(term)
            
            # Check variations (plural, etc.)
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
            
            # Check for variations
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
                diagnosis_text = re.sub(r'\s+', ' ', match.strip())
                if diagnosis_text:
                    # Split multiple diagnoses
                    diagnosis_list = re.split(r'[;\n]|(?:\d+\.)', diagnosis_text)
                    for diag in diagnosis_list:
                        diag = diag.strip().rstrip('.')
                        if len(diag) > 5:
                            diagnoses.append(diag)
        
        # If no structured diagnosis found, look for common patterns
        if not diagnoses:
            diagnosis_keywords = ['diagnosis:', 'impression:', 'findings:', 'conclusion:']
            for keyword in diagnosis_keywords:
                pattern = re.compile(rf'{keyword}\s*(.*?)(?:\n[A-Z]+:|\n\n|\Z)', re.IGNORECASE | re.DOTALL)
                matches = pattern.findall(text)
                for match in matches:
                    cleaned = re.sub(r'\s+', ' ', match.strip())
                    if len(cleaned) > 5:
                        diagnoses.append(cleaned)
        
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
        for procedure in self.procedures:
            if procedure in text_lower:
                procedures.append(procedure)
        
        return list(set(procedures))
    
    def process_report(self, report_text: str, report_id: str) -> ClinicalReport:
        """Process a single report and extract all information"""
        
        codes = self.extract_medical_codes(report_text)
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
        """Process PDF and return structured JSON for all reports"""
        
        if PDF_AVAILABLE:
            full_text = self.extract_text_from_pdf(pdf_path)
        else:
            print(f"PDF processing not available. Please extract text manually from {pdf_path}")
            return []
        
        if not full_text:
            print("No text extracted from PDF")
            return []
        
        reports = self.split_reports(full_text)
        print(f"Found {len(reports)} reports")
        
        results = []
        for i, report_text in enumerate(reports):
            report_id = f"Report {i+1}"
            
            try:
                clinical_report = self.process_report(report_text, report_id)
                
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
    
    extractor = SimpleClinicalExtractor()
    
    # Look for the PDF file
    pdf_path = "Input Data for assignment.pdf"
    
    if not Path(pdf_path).exists():
        print(f"PDF file '{pdf_path}' not found.")
        print("Please place your PDF file in this directory and run again.")
        return
    
    # Process the PDF
    results = extractor.process_pdf(pdf_path)
    
    if results:
        # Save results to JSON file
        output_file = "clinical_extraction_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Extraction complete! Results saved to: {output_file}")
        print(f"Processed {len(results)} reports")
        
        # Display summary
        for result in results:
            print(f"\n📋 {result['ReportID']}:")
            print(f"  🔍 Clinical Terms: {len(result['Clinical Terms'])}")
            print(f"  🫀 Anatomical Locations: {len(result['Anatomical Locations'])}")
            print(f"  🩺 Diagnoses: {len(result['Diagnosis'])}")
            print(f"  ⚕️ Procedures: {len(result['Procedures'])}")
            print(f"  📊 ICD-10 Codes: {len(result['ICD-10'])}")
            print(f"  💼 CPT Codes: {len(result['CPT'])}")
            
            if result['Clinical Terms']:
                print(f"     Clinical Terms: {', '.join(result['Clinical Terms'][:3])}...")
            if result['ICD-10']:
                print(f"     ICD-10: {', '.join(result['ICD-10'])}")
            if result['CPT']:
                print(f"     CPT: {', '.join(result['CPT'])}")

if __name__ == "__main__":
    main() 