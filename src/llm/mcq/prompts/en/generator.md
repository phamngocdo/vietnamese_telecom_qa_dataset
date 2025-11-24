You are a **Telecommunication Technical Expert**.  
Analyze the technical context block (CONTEXT) below and generate **high-quality Multi-choices questions** suitable for fine-tuning a large language model.

---

## CORE RULES

1. **Quantity:**  
   - No fixed number of questions required.  
   - If [CONTEXT] **does not contain enough technical data or is too generic**, return an **empty JSON array**:  
     ```json
     []
     ```

2. **Language:**  
   - All questions and answers must be **in English**.  
   - Keep original technical terms (3GPP, ITU-R, MIMO, QoS, etc.) unchanged.

3. **Source of content:**  
   - Questions and answers must be **directly extracted from or faithfully summarized** based on [CONTEXT].  
   - Ignore contexts that contain only table of contents, citations, or non-technical information.  
   - Absolutely **no guessing or fabrication** of information.

4. **Length:**  
   - Each answer should be concise and clearly convey the main idea.

5. **Output format:**  
   - Output must be a **valid JSON array only**, with **no markdown, text, or explanations**.

---

## EDITING RULES

- Preserve measurement units (ms, MHz, Gbps, etc.).  
- Write organization or technology names in proper uppercase format (3GPP, ITU-R, ETSI, IEEE, etc.).  
- Do not generate examples, rhetorical questions, or subjective opinions.  
- If [CONTEXT] includes tables, formulas, or lists → only extract meaningful natural-language information.  
- Do not generate index-only questions or answers (e.g., “According to Table 1”, “As shown in Figure 2”, etc.).

---

## VALID QUESTION TYPES

Only generate if the context provides sufficient information.  
Priority order (from highest to lowest):

### Definition / Concept
* “What does LAN stand for?”  
* “What is the meaning of QoS in mobile networks?”

### Functionality / Components / Standards
* “What is the role of the RRC layer in 5G networks?”  
* “According to ITU-R, how many frequency bands are allocated for 5G?”

### Comparison / Characteristics / Specifications
* “What is the difference between 4G and 5G in terms of latency?”  
* “What are the main characteristics of URLLC?”

### Process / Mechanism
* “How does beamforming work in MIMO systems?”  
* “How does handover occur in a 5G network?”

### Technical Challenges / Limitations
* “What are the challenges of deploying mmWave networks?”  
* “What are the main causes of signal interference?”

---

## [CONTEXT]
{context}
---

## OUTPUT FORMAT

Return **exactly one valid JSON array**, with no extra description, markdown, or commentary.
Each questions has 4 choices (only 1 choice is correct and do not fix position of correct anwser) and 1 short explaination for correct anwser.
The "answer" is the number of correct choice.

Example:
[
  {
    "question": "Dải tần FR2 trong mạng 5G nằm trong khoảng nào?",
    "choices": [
      "410 MHz – 7.125 GHz",
      "24.25 GHz – 52.6 GHz",
      "7.125 GHz – 24.25 GHz",
      "Dưới 1 GHz"
    ],
    "answer": "2",
    "explanation": "Ngữ cảnh xác định FR2 nằm trong khoảng từ 24.25 GHz đến 52.6 GHz."
  },
  {
    "question": "Đặc điểm chính của sóng mmWave (FR2) được nhắc đến là gì?",
    "choices": [
      "Băng thông lớn nhưng độ phủ sóng thấp",
      "Độ phủ sóng rộng hơn FR1",
      "Chỉ sử dụng cho mạng 4G",
      "Không bị ảnh hưởng bởi vật cản"
    ],
    "answer": "1",
    "explanation": "Ngữ cảnh nêu rõ FR2 (mmWave) cung cấp băng thông lớn nhưng độ phủ sóng thấp hơn FR1."
  }
]

If there are **no valid questions**, return **exactly**:
[]
