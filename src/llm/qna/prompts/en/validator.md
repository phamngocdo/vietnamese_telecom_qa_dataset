# Telecom QA Evaluation Guidelines

Evaluate a list of QA pairs [QA_PAIRS] based on a context block [CONTEXT].

---

## CORE RULES

A QA pair is evaluated as **`true`** (suitable) if it meets ALL of the following conditions:
1.  The question is directly related to the technical content within the [CONTEXT].
2.  The answer is accurate and verifiable **either from the [CONTEXT] OR from your expert telecommunications knowledge (if the context is not clear enough)**.
3.  Contains no vague speculation, fabrication, or information that contradicts technical facts.
4.  The language is clear, precise, and uses correct technical terminology (3GPP, IEEE, QoS, MIMO...).
5.  If there is a conflict between the [CONTEXT] and your knowledge, **prioritize the [CONTEXT]** as the source of truth.

A QA pair is evaluated as **`false`** (unsuitable) if it meets AT LEAST ONE of the following:
1.  The question or answer is unrelated to the [CONTEXT] or the field of telecommunications.
2.  The answer contains information that is verifiably false (against technical facts or the context).
3.  The question/answer is too generic, subjective, or cannot be verified by telecommunications knowledge.
4.  The answer is a null descriptor (e.g., "other types," "remaining items"), especially if the [CONTEXT] is a table, list, or title.

---

## EDITING RULES
* Maintain exact units of measurement (ms, MHz, Gbps...).
* Correctly capitalize standard organization and technology names (3GPP, ITU-R, ETSI, IEEE...).
* If [CONTEXT] contains tables, lists, or formulas $\rightarrow$ only evaluate the part that is understandable as natural language.

---

## INPUT
Input is a single JSON object.

{
  "context": "{context}",
  "qna_counts": "{qna_counts}",
  "qna_list": {qna_list}
}

---

## MANDATORY OUTPUT FORMAT
RETURN ONLY A SINGLE BOOLEAN ARRAY. The array must have {qna_counts} elements.
DO NOT add any explanatory text, greetings, or Markdown. Your response must START with [ and END with ].

---

## EXAMPLES
**Input:**

{
    "context": "IEEE 802.11ax-2021 defines Wi-Fi 6 with high speeds and low latency.",
    "qna_counts": "2",
    "qna_list": [
        { "question": "What standard is IEEE 802.11ax-2021?", "answer": "It is the Wi-Fi 6 standard defined by IEEE to improve speed and reduce network latency."},
        { "question": "Does 6G use MIMO?", "answer": "Yes, 6G is expected to use more advanced MIMO than 5G."}
    ]
}

**Output:**
[true, false]
