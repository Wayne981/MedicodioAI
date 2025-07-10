#!/usr/bin/env python3
"""
Test the simplified clinical extractor with sample medical reports
"""

import json
from simple_clinical_extractor import SimpleClinicalExtractor

# Sample medical reports for testing
SAMPLE_REPORTS = [
    """
COLONOSCOPY REPORT

PATIENT: John Doe
DATE: 2023-10-15

INDICATION: Screening colonoscopy, history of rectal bleeding

PROCEDURE PERFORMED: Total colonoscopy with biopsy

FINDINGS:
The colonoscope was advanced to the cecum. The ileocecal valve was identified.
In the sigmoid colon, multiple diverticula were noted consistent with diverticulosis.
In the rectum, internal hemorrhoids were visualized.
A 5mm polyp was identified in the ascending colon and removed via polypectomy.

DIAGNOSIS:
1. Diverticulosis of sigmoid colon
2. Internal hemorrhoids
3. Adenomatous polyp, ascending colon

PROCEDURE CODES:
CPT: 45378 (Colonoscopy with biopsy)
CPT: 45385 (Colonoscopy with polypectomy)

ICD-10: K57.30 (Diverticulosis of large intestine)
ICD-10: K64.1 (Second degree hemorrhoids)
ICD-10: K63.5 (Polyp of colon)
""",

    """
UPPER ENDOSCOPY REPORT

PATIENT: Jane Smith
DATE: 2023-10-16

INDICATION: Gastroesophageal reflux disease, dysphagia

PROCEDURE PERFORMED: EGD with biopsy

FINDINGS:
The esophagus showed evidence of Barrett's esophagus with intestinal metaplasia.
Erosive esophagitis was noted in the distal esophagus.
The stomach showed mild gastritis in the antrum.
The duodenum appeared normal.

DIAGNOSIS:
1. Barrett's esophagus with intestinal metaplasia
2. Erosive esophagitis, Grade B
3. Chronic gastritis

CPT: 43239 (EGD with biopsy)
ICD-10: K22.70 (Barrett's esophagus without dysplasia)
ICD-10: K21.0 (GERD with esophagitis)
""",

    """
SIGMOIDOSCOPY REPORT

PATIENT: Robert Johnson
DATE: 2023-10-17

PROCEDURE: Flexible sigmoidoscopy

INDICATION: Change in bowel habits, abdominal pain

FINDINGS:
Sigmoid colitis was observed with mucosal erythema and friability.
Sigmoid colon showed inflammatory changes consistent with ulcerative colitis.

DIAGNOSIS:
1. Ulcerative colitis, sigmoid colon

CPT: 45330 (Flexible sigmoidoscopy)
ICD-10: K51.20 (Ulcerative colitis, unspecified)
Modifier: 22 (Increased procedural services)
""",

    """
COLONOSCOPY WITH THERAPEUTIC INTERVENTION

PATIENT: Mary Williams  
DATE: 2023-10-18

PROCEDURE: Colonoscopy with argon plasma coagulation

INDICATION: Follow-up for gastrointestinal bleeding

FINDINGS:
Colonoscopy revealed an arteriovenous malformation in the cecum.
Argon plasma coagulation was applied for hemostasis.
No active bleeding observed post-treatment.

DIAGNOSIS:
1. Arteriovenous malformation, cecum
2. History of gastrointestinal bleeding

CPT: 45382 (Colonoscopy with control of bleeding)
ICD-10: K92.2 (Gastrointestinal hemorrhage)
ICD-10: K55.20 (Angiodysplasia of colon)
HCPCS: C9734 (Focused ultrasound ablation)
"""
]

def test_extractor():
    """Test the clinical extractor with sample reports"""
    
    print("🧪 Testing Simplified Clinical Information Extraction System")
    print("=" * 65)
    
    extractor = SimpleClinicalExtractor()
    
    # Process each sample report
    results = []
    
    for i, report_text in enumerate(SAMPLE_REPORTS):
        report_id = f"Sample Report {i+1}"
        print(f"\n📄 Processing {report_id}...")
        
        try:
            # Process the report
            clinical_report = extractor.process_report(report_text, report_id)
            
            # Convert to JSON format
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
            
            # Print summary
            print(f"   ✅ Clinical Terms: {len(result['Clinical Terms'])}")
            print(f"   ✅ Anatomical Locations: {len(result['Anatomical Locations'])}")
            print(f"   ✅ Diagnoses: {len(result['Diagnosis'])}")
            print(f"   ✅ Procedures: {len(result['Procedures'])}")
            print(f"   ✅ ICD-10 Codes: {len(result['ICD-10'])}")
            print(f"   ✅ CPT Codes: {len(result['CPT'])}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Save test results
    output_file = "sample_extraction_results.json"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Test results saved to: {output_file}")
    except Exception as e:
        print(f"❌ Error saving results: {e}")
    
    # Display detailed results
    print("\n" + "=" * 65)
    print("📊 DETAILED EXTRACTION RESULTS")
    print("=" * 65)
    
    for result in results:
        print(f"\n🏥 {result['ReportID']}")
        print("-" * 45)
        
        print(f"🔍 Clinical Terms ({len(result['Clinical Terms'])}):")
        for term in result['Clinical Terms'][:8]:  # Show first 8
            print(f"   • {term}")
        if len(result['Clinical Terms']) > 8:
            print(f"   ... and {len(result['Clinical Terms']) - 8} more")
        
        print(f"\n🫀 Anatomical Locations ({len(result['Anatomical Locations'])}):")
        for location in result['Anatomical Locations']:
            print(f"   • {location}")
        
        print(f"\n🩺 Diagnoses ({len(result['Diagnosis'])}):")
        for diagnosis in result['Diagnosis']:
            print(f"   • {diagnosis}")
        
        print(f"\n⚕️ Procedures ({len(result['Procedures'])}):")
        for procedure in result['Procedures']:
            print(f"   • {procedure}")
        
        print(f"\n📊 Medical Codes:")
        if result['ICD-10']:
            print(f"   ICD-10: {', '.join(result['ICD-10'])}")
        if result['CPT']:
            print(f"   CPT: {', '.join(result['CPT'])}")
        if result['HCPCS']:
            print(f"   HCPCS: {', '.join(result['HCPCS'])}")
        if result['Modifiers']:
            print(f"   Modifiers: {', '.join(result['Modifiers'])}")
    
    print(f"\n🎉 Successfully processed {len(results)} sample reports!")
    print("💡 This demonstrates the extraction capabilities.")
    print("📄 Ready to process your actual PDF file!")

if __name__ == "__main__":
    test_extractor() 