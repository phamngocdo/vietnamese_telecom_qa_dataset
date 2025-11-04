You are a **Telecommunications Technical Expert**.  
Analyze the following technical context block (**CONTEXT CHUNK**) and generate up to **no limited high-quality Question–Answer (QA) pairs** suitable for fine-tuning a language model.

---

## CORE RULES

1. **Quantity:**  
   - Generate **up to 3** QA pairs.  
   - If the [CONTEXT CHUNK] **lacks technical information or is too generic**, return an **empty JSON array**:  
     ```json
     []
     ```

2. **Language:**  
   - All questions and answers must be **in Vietnamese**.  
   - **Keep original abbreviations and technical terms** (e.g., 3GPP, ITU-R, MIMO, QoS).

3. **Content Source:**  
   - Each QA must be **faithfully extracted or summarized** from the [CONTEXT CHUNK].  
   - **Do not invent, assume, or hallucinate** any information.

4. **Length:**  
   - Each answer should be concise and complete.

5. **Output Format:**  
   - Output **only one valid JSON array**.  
   - **No Markdown, no extra text, no explanations.**

---

## EDITING RULES

- Keep measurement units (ms, MHz, Gbps, etc.) unchanged.  
- Technical or organizational names must remain capitalized (3GPP, ITU-R, ETSI, IEEE…).  
- Do **not** generate examples, rhetorical questions, or subjective comments.  
- If the [CONTEXT CHUNK] contains tables, formulas, or lists → extract only the parts that can be expressed in natural language.

---

## VALID QUESTION TYPES

Generate questions **only if enough context is available.**  
Priority order (high → low):

### Definition

### Functionality & Standards

### Comparison & Characteristics

### Process & Mechanism

### Challenges & Limitations

---

## [CONTEXT CHUNK]
---
{context_chunk}
---

## OUTPUT FORMAT
```json
[
  {"question": "Khái niệm QoS trong mạng di động là gì?", "answer": "QoS là chất lượng dịch vụ đảm bảo hiệu năng mạng."},
  {"question": "Mục tiêu của 5G NR là gì?", "answer": "Đáp ứng các yêu cầu băng thông, độ trễ thấp và kết nối lớn."}
]

If there are no valid QA pairs, output only:
```json
[]
```