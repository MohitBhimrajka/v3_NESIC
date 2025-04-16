# prompt_testing.py

import textwrap

# --- Standard Instruction Blocks ---

# ADDITIONAL REFINED INSTRUCTIONS: Incorporates stronger measures for accuracy, table formatting, single-entity coverage, etc.
ADDITIONAL_REFINED_INSTRUCTIONS = textwrap.dedent("""\
    **Additional Refined Instructions for Zero Hallucination, Perfect Markdown, and Strict Single-Entity Coverage:**

    *   **Dedicated No-Output Fallback if Missing Sources:**
        1. If no valid Vertex AI grounding URLs exist for a required factual point or section, omit that data entirely (do not guess or fabricate).
        2. In the relevant subsection, explicitly state: "No verifiable data found [SSX], omitted due to missing official grounding."
        3. If a table is requested but data is unavailable, provide a placeholder row or empty table noting "No verifiable data found [SSX]."

    *   **Mandatory Self-Check Before Final Output:**
        - Before producing the final answer, confirm:
            1. All requested sections are fully included.
            2. All factual statements have inline citations [SSX] pointing to valid Vertex AI URLs in the final Sources list.
            3. Only the permitted Vertex AI grounding URLs are used—no external or fabricated links.
            4. Markdown headings and tables follow the specified format (##, ###, consistent columns).
            5. A single "Sources" section is present, properly labeled, and each source is on its own line.
            6. Inline citations appear before punctuation where feasible.
            7. No data or sources are invented.
            8. Strictly reference only the exact named company; do not include similarly named entities.

    *   **Exactness of Table Columns:**
        - Each row in any table must have the same number of columns as the header row.
        - If data is missing, insert "-" or "(No Data)" but keep the columns aligned.
        - Always include an inline citation if referencing factual numbers.

    *   **Quotes with Inline Citations:**
        - Any verbatim quote must include:
            1. The speaker's name and date or document reference in parentheses.
            2. An inline citation [SSX] immediately following.
        - This ensures clarity on who said it, when they said it, and the exact source.

    *   **Exactness of Hyperlinks in Sources:**
        - The final "Sources" section must use the format "* [Supervity Source X](Full_URL) - Brief annotation [SSX]."
        - Number sources sequentially without skipping.
        - Provide no additional domain expansions or transformations beyond what is given.
        - Do not summarize entire documents—only note which facts the source supports.

    *   **Do Not Summarize Sources:**
        - In each source annotation, reference only the specific claim(s) the link supports, not a broad summary.

    *   **Placeholders for Non-Public Data:**
        - If certain requested info cannot be verified, omit it entirely or label it succinctly as "(No Public Data Found) [SSX]."
        - Maintain consistent formatting in either case.

    *   **High-Priority Checklist (Must Not Be Violated):**
        1. No fabrication: Omit rather than invent ungrounded data.
        2. Adhere strictly to the specified Markdown formats (headings, lists, tables).
        3. Use inline citations [SSX] matching final sources exactly.
        4. Provide only one "Sources" section at the end.
        5. Do not use any URLs outside "vertexaisearch.cloud.google.com/..." pattern if not explicitly provided.
        6. Enforce single-entity coverage: if "Marvel Inc." is the focus, do not include other similarly named entities.
        7. Complete an internal self-check to ensure compliance with all instructions before concluding.
""")

# FINAL SOURCE LIST INSTRUCTIONS: Revised to require inline citation linkage.
FINAL_SOURCE_LIST_INSTRUCTIONS_TEMPLATE = textwrap.dedent("""\
    **Final Source List Requirements:**

    Conclude the *entire* research output, following the 'General Discussion' paragraph, with a clearly marked section titled "**Sources**". This section is critical for verifying the information grounding process AND for document generation.

    **1. Content - MANDATORY URL Type & Source Integrity:**
    *   **Exclusive Source Type:** This list **MUST** contain *only* the specific grounding redirect URLs provided directly by the **Vertex AI Search system** *for this specific query*. These URLs represent the direct grounding evidence used.
    *   **URL Pattern:** These URLs typically follow the pattern: `https://vertexaisearch.cloud.google.com/grounding-api-redirect/...`. **Only URLs matching this exact pattern are permitted.**
    *   **Strict Filtering:** Absolutely **DO NOT** include any other type of URL (direct website links, news, PDFs, etc.).
    *   **CRITICAL - No Hallucination:** **Under NO circumstances should you invent, fabricate, infer, or reuse `vertexaisearch.cloud.google.com/...` URLs** from previous queries or general knowledge if they were not explicitly provided as grounding results *for this query*. If a fact is identified but lacks a corresponding provided grounding URL, it must be omitted.
    *   **Purpose:** This list verifies the specific grounding data provided by Vertex AI Search for this request—not external knowledge or other URLs.

    **2. Formatting and Annotation (CRITICAL FOR PARSING):**
    *   **Source Line Format:** Present each source on a completely new line. Each line **MUST** start with a Markdown list indicator (`* ` or `- `) followed by the hyperlink in Markdown format and then its annotation.
    *   **REQUIRED Format:** 
        ```markdown
        * [Supervity Source X](Full_Vertex_AI_Grounding_URL) - Annotation explaining exactly what information is supported (e.g., supports CEO details and FY2023 revenue [SSX]).
        ```
    *   **Sequential Labeling:** The visible hyperlink text **MUST** be labeled sequentially "Supervity Source 1", "Supervity Source 2", etc. Do not skip numbers.
    *   **Annotation Requirement:** The annotation MUST be:
        * Included immediately after the hyperlink on the same line, separated by " - ".
        * Brief and specific, explaining exactly which piece(s) of information in the main body (and referenced with inline citation [SSX]) that grounding URL supports.
        * Written in the target output language: **{language}**.

    **3. Quantity and Linkage:**
    *   **Target Quantity:** Aim for a minimum of 5 and a maximum of 18 distinct, verifiable Vertex AI grounding URLs that directly support content in the report.
    *   **Accuracy Over Quantity:** Accuracy and adherence to the grounding rules are absolute. If fewer than 5 verifiable URLs are available from the provided results, list only those.
    *   **Fact Linkage:** Every grounding URL listed MUST directly correspond to facts/figures/statements present in the report body. The annotation must clearly link to the inline citation(s) [SSX] used in the text.

    **4. Content Selection Based on Verifiable Grounding:**
    *   **Prerequisite for Inclusion:** Only include facts, figures, details, or quotes in the main report if they can be supported by a verifiable Vertex AI grounding URL from this query.
    *   **Omission of Ungrounded Facts/Sections:** If specific information cannot be supported by a verifiable grounding URL, omit that detail. If a whole section cannot be grounded, omit the entire section.

    **5. Final Check:**
    *   Before concluding the response, review the entire output. Verify:
        * Exclusive use of valid, provided Vertex AI grounding URLs.
        * Each source is on a new line and follows the correct format.
        * Every fact in the report body is supported by an inline citation [SSX] that corresponds to a source in this list.
    *   The "**Sources**" section must appear only once, at the end of the entire response.
    """)

# HANDLING MISSING INFORMATION: Revised to enforce strict omission if grounding is unavailable.
HANDLING_MISSING_INFO_INSTRUCTION = textwrap.dedent("""\
    *   **Handling Missing or Ungrounded Information:**
        *   **Exhaustive Research First:** Conduct exhaustive research using primarily official company sources (see `RESEARCH_DEPTH_INSTRUCTION`).
        *   **Grounding Requirement for Inclusion:** Information is included only if:
            1. The information is located in a reliable source document.
            2. A corresponding, verifiable Vertex AI grounding URL (matching the pattern `https://vertexaisearch.cloud.google.com/grounding-api-redirect/...`) is provided in the search results for this query.
        *   **Strict Omission Policy:** If information cannot meet both conditions, omit that specific fact or section entirely. Do not use placeholders such as 'N/A' or 'Not Found'.
        *   **No Inference/Fabrication:** Do not infer, guess, or estimate ungrounded information. Do not fabricate grounding URLs.
        *   **Cross-Language Search:** If necessary, check other language results; if found, translate only the necessary information and list the corresponding grounding URL.
    """)

# RESEARCH DEPTH & CALCULATION: Revised to include forbidden sources and conflict handling.
RESEARCH_DEPTH_INSTRUCTION = textwrap.dedent("""\
    *   **Research Depth & Source Prioritization:**
        *   **Exhaustive Search:** Conduct thorough research for all requested information points. Dig beyond surface-level summaries.
        *   **Primary Source Focus:** Use official company sources primarily, including:
            * Latest Annual / Integrated Reports (and previous years for trends)
            * Official Financial Statements (Income Statement, Balance Sheet, Cash Flow) & Crucially: Footnotes
            * Supplementary Financial Data, Investor Databooks, Official Filings (e.g., EDINET, SEC filings, local equivalents)
            * Investor Relations Presentations & Materials (including Mid-Term Plans, Strategy Day presentations)
            * Earnings Call Transcripts & Presentations (focus on Q&A sections)
            * Official Corporate Website sections (e.g., "About Us", "Investor Relations", "Strategy", "Governance", "Sustainability/ESG")
            * Official Press Releases detailing strategy, financials, organizational structure, or significant events.
        *   **Forbidden Sources:** Do NOT use:
            * Wikipedia
            * Generic blogs, forums, or social media posts
            * Press release aggregation sites (unless linking directly to an official release)
            * Outdated market reports (unless historical context is explicitly requested)
            * Competitor websites/reports (except in competitive analysis with caution)
            * Generic news articles unless they report specific, verifiable events from highly reputable sources (e.g., Nikkei, Bloomberg, Reuters, FT, WSJ).
        *   **Emphasize Primary Sources:** Primary documents provide accuracy, official positioning, and verifiability.
        *   **Management Commentary:** Actively incorporate direct management commentary and analysis from these sources.
        *   **Recency:** Focus on the most recent 1-2 years for qualitative analysis; use the last 3 full fiscal years for financial trends. Clearly state the reporting period.
        *   **Secondary Sources:** Use reputable secondary sources sparingly for context or verification, always with clear attribution.
        *   **Handling Conflicts:** If conflicting information is found between official sources, prioritize the most recent, definitive source. Note discrepancies with dual citations if significant (e.g., [SSX, SSY]).
        *   **Calculation Guidelines:** If metrics are not explicitly reported but must be calculated:
            * Calculate only if all necessary base data (e.g., Net Income, Revenue, Equity, Assets, Debt) is available and verifiable.
            * Clearly state the formula used, and if averages are used, mention that.
        *   **Confirmation of Unavailability:** Only conclude information is unavailable after a diligent search across multiple primary sources.
    """)

# ANALYSIS & SYNTHESIS INSTRUCTION: Revised to encourage explicit "why" analysis and linking.
ANALYSIS_SYNTHESIS_INSTRUCTION = textwrap.dedent("""\
    *   **Analysis and Synthesis:**
        *   Beyond listing factual information, provide concise analysis where requested (e.g., explain trends, discuss implications, identify drivers, assess effectiveness).
        *   **Explicitly address "why":** For every data point or trend, explain why it is occurring or what the key drivers are.
        *   **Comparative Analysis:** Compare data points (e.g., YoY changes, company performance against competitors) where appropriate.
        *   **Linking Information:** In the General Discussion, explicitly tie together findings from different sections to present a coherent overall analysis (e.g., link financial performance with strategic initiatives).
    """)

# INLINE CITATION INSTRUCTION: Mandate inline citations for all factual claims.
INLINE_CITATION_INSTRUCTION = textwrap.dedent("""\
    *   **Inline Citation Requirement:**
        *   Every factual claim, data point, and specific summary must include an inline citation in the format [SSX], where X corresponds exactly to the sequential number of the source in the final Sources list.
        *   Place the inline citation immediately after the supported statement and before punctuation when possible.
        *   If a single source supports multiple facts, reuse the same [SSX].
        *   This ensures that each fact is directly verifiable against the corresponding "Supervity Source X" in the final Sources list.
    """)

# SPECIFICITY INSTRUCTION: Instruct to include specific dates, definitions, and quantification.
SPECIFICITY_INSTRUCTION = textwrap.dedent("""\
    *   **Specificity and Granularity:**
        *   For all time-sensitive data points (e.g., financials, employee counts, management changes), include specific dates or reporting periods (e.g., "as of 2024-03-31", "for FY2023").
        *   Define any industry-specific or company-specific terms or acronyms on their first use.
        *   Quantify qualitative descriptions with specific numbers or percentages where available (e.g., "growth of 12% [SSX]").
        *   List concrete examples rather than vague categories when describing initiatives, strategies, or risks.
    """)

# AUDIENCE CONTEXT REMINDER
AUDIENCE_CONTEXT_REMINDER = textwrap.dedent("""\
    *   **Audience Relevance:** Keep the target audience (Japanese corporate strategy professionals) in mind. Frame analysis and the 'General Discussion' to highlight strategic implications, competitive positioning, market opportunities/risks, and operational insights relevant for potential partnership, investment, or competitive assessment.
    """)

# STANDARD OUTPUT LANGUAGE INSTRUCTION
def get_language_instruction(language: str) -> str:
    return f"Output Language: The final research output must be presented entirely in **{language}**."

# BASE_FORMATTING_INSTRUCTIONS: Revised to include logical flow and conciseness.
BASE_FORMATTING_INSTRUCTIONS = textwrap.dedent("""\
    Output Format & Quality Requirements:

    *   **Direct Start & No Conversational Text:** Begin the response directly with the first requested section heading (e.g., `## 1. Core Corporate Information`). No introductory or concluding remarks are allowed.
    
    *   **Strict Markdown Formatting Requirements:**
        *   Use valid and consistent Markdown throughout the entire document.
        *   **Section Formatting:** Sections MUST be numbered exactly as specified in the prompt (e.g., `## 1. Core Corporate Information`).
        *   **Subsection Formatting:** Use `###` for subsections and maintain hierarchical structure (e.g., `### CEO Name, Title`).
        *   **List Formatting:** Use asterisks (`*`) or hyphens (`-`) for bullets with consistent indentation (4 spaces for sub-bullets).
        *   **Tables:** Format all tables with proper Markdown table syntax:
            ```markdown
            | Header 1 | Header 2 | Header 3 |
            |----------|----------|----------|
            | Data 1   | Data 2   | Data 3   |
            | Data 4   | Data 5   | Data 6   |
            ```
        *   **Code Blocks:** Use triple backticks (```) for code blocks when presenting technical details.
        *   **Quotes:** Use Markdown quote syntax (>) for direct quotations from executives when appropriate.
    
    *   **Optimal Structure & Readability:**
        *   Present numerical data in tables with proper alignment and headers.
        *   Use bullet points for lists of items or characteristics.
        *   Use paragraphs for narrative descriptions and analysis.
        *   Maintain consistent formatting across similar elements throughout the document.
        *   **Content Organization:** Ensure a logical sequence within each section (e.g., chronological order for trends, priority order for lists).
        *   **Conciseness:** Provide detailed yet concise language—be specific without unnecessary verbosity.
    
    *   **Data Formatting Consistency:**
        *   Use appropriate thousands separators for numbers per the target language: **{language}**.
        *   **Currency Specification:** Always specify the currency (e.g., ¥, $, €, JPY, USD, EUR) for all monetary values along with the reporting period.
        *   Format dates in a consistent style (e.g., YYYY-MM-DD).
        *   Use consistent percentage formatting (e.g., 12.5%).
    
    *   **Table Consistency Requirements:**
        *   All tables must have header rows with clear column titles.
        *   Include a separator row (|---|---|) between headers and data.
        *   Align column content appropriately (left for text, right for numbers).
        *   Maintain the same number of columns throughout each table.
        *   Include units in column headers where applicable (e.g., "Revenue (JPY millions)").
    
    *   **Section Completion Verification:**
        *   Every section requested in the prompt MUST be included in the output.
        *   Sections must appear in the exact order specified in the prompt.
        *   Each section must be properly labeled with the exact heading from the prompt.
        *   Incomplete sections should be explicitly marked as having partial data rather than omitted entirely.
    
    *   **Tone and Detail Level:**
        *   Maintain a professional, objective, and analytical tone suited for a Japanese corporate strategy audience.
        *   Provide granular detail (e.g., figures, dates, metrics) while avoiding promotional language.
    
    *   **Completeness and Verification:**
        *   Address all requested points in each section.
        *   Verify that every section, the General Discussion, and the Sources list are present and adhere to the instructions.
        *   Perform a final internal review before output.

    *   **Sources List:** The Sources list must be present and adhere to the instructions.
        *   The Sources section should have a header with the text "Sources"
        *   The Sources section should be formatted as a Markdown unordered list.
        *   The Sources section should have a link to the source with the text "Source X" where X is the source number.
                                               
    *   **Inline Citation & Specificity:** Incorporate the inline citation [SSX] for every factual claim (see Inline Citation Requirement) and include specific dates/definitions (see Specificity and Granularity).
    """)

# FINAL REVIEW INSTRUCTION
FINAL_REVIEW_INSTRUCTION = textwrap.dedent("""\
    *   **Internal Final Review:** Before generating the 'Sources' list, review your generated response for:
    
        *   **Completeness Check:**
            * Every numbered section requested in the prompt is present
            * Each section contains all requested subsections and information points
            * The "General Discussion" paragraph is included
            * No sections have been accidentally omitted or truncated
        
        *   **Formatting Verification:**
            * All line breaks are properly formatted
            * All section headings use correct Markdown format (`## Number. Title`)
            * All subsections use proper hierarchical format (`###` or indented bullets)
            * Tables have proper headers, separators, and consistent columns
            * Lists use consistent formatting and indentation
        
        *   **Citation Integrity:**
            * Every factual claim has an inline citation [SSX]
            * Citations are placed immediately after the supported claim
            * All citations correspond to entries in the final Sources list
        
        *   **Data Precision:**
            * All monetary values specify currency and reporting period
            * All dates are in consistent format
            * Numerical data is presented with appropriate precision and units
        
        *   **Content Quality:**
            * Direct start with no conversational text
            * Professional tone with no placeholders or ambiguous statements
            * Adherence to missing info handling instructions
            * Logical flow within and between sections
        
        *   **Single-Entity Coverage:**
            * Ensure that only the specified company name is used and no similarly named entities are included unless they are verifiably the same entity.
        
        Proceed to generate the final 'Sources' list only after confirming these conditions are met.
    """)

# Template for ensuring complete and properly formatted output
COMPLETION_INSTRUCTION_TEMPLATE = textwrap.dedent("""\
    **Output Completion Requirements:**
    
    Before concluding your response, verify that:
    1. Every numbered section requested in the prompt is complete with all required subsections
    2. All content follows proper markdown formatting throughout
    3. Each section contains all necessary details and is not truncated
    4. The response maintains consistent formatting for lists, tables, and code blocks
    5. All inline citations [SSX] are properly placed, with no extraneous or fabricated URLs
    6. Strictly focus on the exact named company (no confusion with similarly named entities)
""")

# --- Prompt Generating Functions ---

def get_basic_prompt(company_name: str, language: str = "Japanese"):
    """Generates a prompt for a comprehensive basic company profile with all enhancements."""
    language_instruction = get_language_instruction(language)
    final_source_instructions = FINAL_SOURCE_LIST_INSTRUCTIONS_TEMPLATE.format(language=language)
    formatting_instructions = BASE_FORMATTING_INSTRUCTIONS.format(language=language)
    completion_instructions = COMPLETION_INSTRUCTION_TEMPLATE
    
    return f"""
Comprehensive Corporate Profile, Strategic Overview, and Organizational Analysis of {company_name}

Objective: To compile a detailed, accurate, and analytically contextualized corporate profile, strategic overview, organizational structure analysis, and key personnel identification for {company_name}, focusing solely on this entity. Avoid detailed analysis of parent or subsidiary companies except for listing subsidiaries as requested.

Target Audience Context: The final research output is intended for review and strategic planning by a **Japanese company**. Present the information clearly and accurately with granular details and actionable insights. {AUDIENCE_CONTEXT_REMINDER}

{language_instruction}

Research Requirements:
Conduct in-depth research using {company_name}'s official sources. Every factual claim, data point, and summary must include an inline citation in the format [SSX] (see Inline Citation Requirement). Provide specific dates or reporting periods (e.g., "as of 2024-03-31", "for FY2023"). Ensure every claim is grounded by a verifiable Vertex AI grounding URL referenced back in the final Sources list.
{HANDLING_MISSING_INFO_INSTRUCTION.format(language=language)}
{RESEARCH_DEPTH_INSTRUCTION}
{SPECIFICITY_INSTRUCTION}
{INLINE_CITATION_INSTRUCTION}
{ANALYSIS_SYNTHESIS_INSTRUCTION}

## 1. Core Corporate Information:
    *   **Stock Ticker Symbol / Security Code:** (if publicly traded) [SSX]
    *   **Primary Industry Classification:** (e.g., GICS, SIC – specify the standard) [SSX]
    *   **Full Name and Title of Current CEO:** [SSX]
    *   **Full Registered Headquarters Address:** [SSX]
    *   **Main Corporate Telephone Number:** [SSX]
    *   **Official Corporate Website URL:** [SSX]
    *   **Date of Establishment/Incorporation:** (e.g., "established on YYYY-MM-DD") [SSX]
    *   **Date of Initial Public Offering (IPO)/Listing:** (if applicable, include exact date) [SSX]
    *   **Primary Stock Exchange/Market where listed:** (if applicable) [SSX]
    *   **Most Recently Reported Official Capital Figure:** (specify currency and reporting period) [SSX]
    *   **Most Recently Reported Total Number of Employees:** (include reporting date and source; quantify any significant changes) [SSX]

## 2. Recent Business Overview:
    *   Provide a detailed summary of {company_name}'s core business operations and primary revenue streams based on the most recent official reports [SSX]. Include specific product or service details and any recent operational developments (with exact dates or periods).
    *   Include key highlights of recent business performance (e.g., "revenue increased by 12% in FY2023 [SSX]") or operational changes (e.g., restructuring, new market entries with dates), and explain their significance [SSX].

## 3. Business Environment Analysis:
    *   Describe the current market environment by identifying major competitors and market dynamics (include specific names, market share percentages, and exact data dates as available [SSX]).
    *   Identify and explain key industry trends (e.g., technological shifts, regulatory changes) including specific figures or percentages where possible [SSX].
    *   ***Discuss the strategic implications and opportunities/threats these trends pose for {company_name} from a Japanese corporate perspective [SSX].***

## 4. Organizational Structure Overview:
    *   Describe the high-level organizational structure as stated in official sources (e.g., "divisional", "functional", "matrix") and reference the source (e.g., "as shown in the Annual Report, p. XX") [SSX].
    *   Briefly comment on the rationale behind the structure and its implications for decision-making and agility [SSX].

## 5. Key Management Personnel & Responsibilities:
    *   **Board of Directors:** List members, their titles, committee memberships, and key responsibilities (preferably in a table if the list is long) with exact dates of appointment or tenure where available [SSX].
    *   **Corporate Auditors / Audit & Supervisory Board Members:** List members with their primary oversight roles [SSX].
    *   **Executive Officers (Management Team):** List key members (beyond CEO) with titles and detailed descriptions of their strategic responsibilities (include start dates and any recent changes with explanation, if available) [SSX].

## 6. Subsidiaries List:
    *   List major direct subsidiaries (global where applicable) based solely on official documentation. For each subsidiary, include primary business activity, country of operation, and, if available, ownership percentage as stated in the source [SSX]. Present this in a table if clarity is needed.

## 7. Leadership Strategic Outlook (Verbatim Quotes):
    *   **CEO & Chairman:** Provide at least four direct, meaningful quotes focusing on long-term vision, key challenges, growth strategies, and market outlook. Each quote must be followed immediately by its source citation in parentheses (e.g., "(Source: Annual Report 2023, p.5)"), and an inline citation [SSX] should be included where the quote supports specific claims in the analysis.
    *   **Other Key Executives (e.g., CFO, CSO, CTO, Regional Heads):** Provide at least three direct quotes each with similar detailed attribution and inline citation [SSX] where applicable.
    
## 8. General Discussion:
    *   Provide a concluding single paragraph (approximately 300-500 words).
    *   **Synthesize** the key findings exclusively from Sections 1-7, explicitly linking analysis (e.g., "The declining revenue margin [SSX] suggests...") and ensuring every claim is supported by an inline citation.
    *   Structure your analysis logically by starting with an overall assessment, then discussing strengths and opportunities, followed by weaknesses and risks, and concluding with an outlook relevant for the Japanese audience.
    *   **Do not introduce new factual claims** that are not derived from the previous sections.

Source and Accuracy Requirements:
*   **Accuracy:** All information must be factually correct, current, and verifiable against grounded sources. Specify currency and reporting periods for all monetary data.
*   **Source Specificity (Traceability):** Every data point, claim, and quote must be traceable to a specific source using an inline citation (e.g., [SSX]). These must match the final Sources list.
*   **Source Quality:** Use only official company sources primarily. Secondary sources may be used sparingly for context. All sources must be clearly cited.

{completion_instructions}
{FINAL_REVIEW_INSTRUCTION}
{final_source_instructions}
{formatting_instructions}
""".strip()


def get_financial_prompt(company_name: str, language: str = "Japanese"):
    """Generates a prompt for a detailed financial analysis with all enhancements."""
    language_instruction = get_language_instruction(language)
    final_source_instructions = FINAL_SOURCE_LIST_INSTRUCTIONS_TEMPLATE.format(language=language)
    formatting_instructions = BASE_FORMATTING_INSTRUCTIONS.format(language=language)
    completion_instructions = COMPLETION_INSTRUCTION_TEMPLATE
    enhanced_financial_research_instructions = textwrap.dedent(f"""\
    *   **Mandatory Deep Search & Calculation:** Conduct an exhaustive search within {company_name}'s official financial disclosures for the last 3 fiscal years, including Annual Reports, Financial Statements (Income Statement, Balance Sheet, Cash Flow Statement), Footnotes, Supplementary Data Packs, official filings, and IR materials. Do not rely solely on summary tables; examine detailed statements and notes for definitions and components [SSX].
    *   **Calculation Obligation:** For financial metrics such as Margins, ROE, ROA, Debt-to-Equity, and ROIC: if not explicitly stated, calculate them using standard formulas only if all necessary base data is available and verifiable. Clearly state the calculation method and any averages used (e.g., "ROE (Calculated: Net Income / Average Shareholders' Equity)") [SSX].
    *   **Strict Omission Policy:** If a metric cannot be found or reliably calculated, omit that specific line item entirely. Never use placeholders like 'N/A' [SSX].
    """)
    return f"""
Comprehensive Strategic Financial Analysis of {company_name} (Last 3 Fiscal Years)

Objective: Deliver a complete, analytically rich, and meticulously sourced financial profile of **{company_name}** using the last three full fiscal years. Combine traditional financial metrics with analysis of profitability, cost structure, cash flow, investments, and contextual factors.

Target Audience Context: This analysis is for a **Japanese corporate strategy audience**. Use Japanese terminology when appropriate (e.g., "売上総利益" for Gross Profit) and ensure that all monetary values specify currency and reporting period (e.g., "FY2023") with exact dates where available [SSX]. {AUDIENCE_CONTEXT_REMINDER}

{language_instruction}

Research Requirements:
For each section, provide verifiable data with inline citations [SSX] and specific dates or reporting periods. Every claim must be traceable to a final source.
{HANDLING_MISSING_INFO_INSTRUCTION.format(language=language)}
{RESEARCH_DEPTH_INSTRUCTION}
{SPECIFICITY_INSTRUCTION}
{INLINE_CITATION_INSTRUCTION}
{enhanced_financial_research_instructions}
{ANALYSIS_SYNTHESIS_INSTRUCTION}

## 1. Top Shareholders:
    *   List major shareholders (typically the top 5-10, with exact ownership percentages, reporting dates, and source references) [SSX].
    *   Briefly comment on the stability or influence of the ownership structure on the financial strategy [SSX].

## 2. Key Financial Metrics (3-Year Trend in a Table):
    *   Present the following metrics for the last 3 fiscal years in a Markdown table. Specify currency and fiscal year for each value. If calculated, show the formula.
        *   Total Revenue / Net Sales
        *   Gross Profit *(Calculated if needed: Revenue - COGS)*
        *   Gross Profit Margin (%) *(Calculated: Gross Profit / Revenue)*
        *   EBITDA and EBITDA Margin (%) *(calculated if possible)*
        *   Operating Income / Operating Profit and Operating Margin (%)
        *   Ordinary Income / Pre-Tax Income and Ordinary Income Margin (%)
        *   Net Income and Net Income Margin (%)
        *   ROE (%) *(calculated as Net Income / Average Shareholders' Equity)*
        *   ROA (%) *(calculated as Net Income / Average Total Assets)*
        *   Total Assets and Total Shareholders' Equity
        *   Equity Ratio (Total Equity / Total Assets)
        *   Key Debt Metrics (e.g., Total Debt and Debt-to-Equity Ratio)
        *   Key Cash Flow Figures (e.g., Net Cash from Operations, Investing, Financing)
    *   Briefly explain any key trends (e.g., a 12% increase in revenue [SSX]) and the potential drivers behind them [SSX].

## 3. Profitability Analysis (3-Year Trend):
    *   Analyze trends in Operating Margin and Net Income Margin, including year-over-year percentage changes. Explain the drivers behind these trends (e.g., cost variations, pricing power) with inline citations [SSX].

## 4. Segment-Level Performance (if applicable):
    *   If segment data is available, present revenue, operating profit, and margin percentages for each segment in a table (include currency and fiscal year) [SSX].
    *   Analyze trends and the relative contribution of each segment, citing specific figures [SSX].

## 5. Cost Structure Analysis (3-Year Trend):
    *   Detail the composition and trends of major operating costs:
        *   Cost of Goods Sold (COGS) and its percentage of revenue.
        *   SG&A expenses and their percentage of revenue.
        *   If available, break down SG&A (e.g., R&D, personnel, marketing) with currency specifications.
    *   Analyze drivers behind cost trends and comment on cost control effectiveness [SSX].

## 6. Cash Flow Statement Analysis (3-Year Trend):
    *   Analyze trends in Operating Cash Flow (OCF) and their drivers (e.g., profit changes versus working capital adjustments).
    *   Detail major Investing and Financing Cash Flow activities with currency and context.
    *   Calculate and analyze Free Cash Flow (FCF = OCF - CapEx) and comment on the company's capacity to fund operations and investments [SSX].

## 7. Investment Activities (Last 3 Years):
    *   Describe major M&A deals, capital expenditure patterns, and any corporate venture or R&D investments with specific amounts (specify currency and reporting period) [SSX].
    *   Analyze the strategic rationale and potential financial impact of these investments [SSX].

## 8. Contextual Financial Factors:
    *   Identify significant one-time events (e.g., asset sales, restructurings) with specific dates and financial impacts [SSX].
    *   Discuss any accounting standard changes and external economic or regulatory influences, with detailed source citations [SSX].
    *   Critically analyze the quality and sustainability of reported earnings and link these factors to performance trends [SSX].

## 9. Credit Ratings & Financial Health (if available):
    *   List current and historical credit ratings (with reporting dates) and summarize key highlights from agency commentary [SSX].
    *   Analyze the implications of these ratings for financial flexibility and cost of capital [SSX].

## General Discussion:
    *   Provide a concluding single paragraph (300-500 words) that synthesizes the findings exclusively from Sections 1-9. Explicitly connect the analysis (e.g., "the declining margin [SSX] suggests...") and explain why these trends exist.
    *   Structure the discussion logically by starting with an overall assessment of financial health, then discussing key trends and deviations, and conclude with an outlook tailored to a Japanese audience.
    *   Do not introduce any new factual claims that are not supported by previous sections.

Source and Accuracy Requirements:
*   **Accuracy:** All information must be current and verifiable. Specify currency and reporting period for every monetary value.
*   **Source Specificity:** Every data point must include an inline citation [SSX] that corresponds to a specific source in the final Sources list.
*   **Source Quality:** Rely primarily on official company sources. Secondary sources may be used sparingly for context and must be clearly cited.

{completion_instructions}
{FINAL_REVIEW_INSTRUCTION}
{final_source_instructions}
{formatting_instructions}
""".strip()


def get_competitive_landscape_prompt(company_name: str, language: str = "Japanese"):
    """Generates a prompt for a detailed competitive analysis with nuanced grounding rules."""
    language_instruction = get_language_instruction(language)
    final_source_instructions = FINAL_SOURCE_LIST_INSTRUCTIONS_TEMPLATE.format(language=language)
    formatting_instructions = BASE_FORMATTING_INSTRUCTIONS.format(language=language)
    completion_instructions = COMPLETION_INSTRUCTION_TEMPLATE
    competitive_research_instructions = textwrap.dedent(f"""\
    **Research & Grounding Strategy for Competitive Analysis:**

    1.  **Prioritize Grounded Facts:** Conduct exhaustive research using Vertex AI Search. Include facts, figures, and competitor details directly supported by provided grounding URLs, each referenced with an inline citation [SSX].
    2.  **Handling Synthesis and Secondary Information:** For analysis that uses information not directly grounded by a Vertex AI URL, clearly indicate the source next to the information (e.g., "Source: Nikkei Asia, 2024-03-15"). Such secondary data should not appear in the final Sources list.
    3.  **Omission Rule:** Omit any factual claim that lacks direct grounding via a verified URL. Analytical or synthesized data must clearly reference all sources inline [SSX].
    4.  **Focus on Verifiable Data:** Ensure accuracy by using only officially grounded and verifiable information. If competitor details come from dubious sources, omit them.
    5.  **Final Source List Integrity:** The final "Sources" list must include only the Vertex AI grounding URLs provided for this query, and inline citations [SSX] must match these sources.
    """)
    return f"""
Detailed Competitive Analysis and Strategic Positioning of {company_name}

Objective: To conduct a comprehensive competitive analysis of **{company_name}** by identifying key competitors, analyzing their market share, strengths, weaknesses, and strategic moves, and outlining {company_name}'s competitive positioning. Conclusions should include a synthesized discussion relevant to a Japanese corporate audience.

Target Audience Context: This output is for strategic review by a **Japanese company**. Ensure all analysis is supported by explicit inline citations [SSX] and that secondary data is clearly attributed if used. {AUDIENCE_CONTEXT_REMINDER}

{language_instruction}

{HANDLING_MISSING_INFO_INSTRUCTION.format(language=language)}
{RESEARCH_DEPTH_INSTRUCTION}
{SPECIFICITY_INSTRUCTION}
{INLINE_CITATION_INSTRUCTION}
{competitive_research_instructions}

{ANALYSIS_SYNTHESIS_INSTRUCTION}

## 1. Major Competitors Identification & Profiling:
    *   Identify primary global and key regional competitors from reliable official sources. Provide specific names, market share percentages, and exact data dates with inline citations [SSX].
    *   For each competitor:
        *   **Full Name & Brief Description:** Outline their operations and scale with verifiable details [SSX].
        *   **Estimated/Reported Market Share:** Provide market share data along with the market and period, using inline citations [SSX].
        *   **Key Geographic Areas of Overlap:** Detail where they compete directly with {company_name} [SSX].
        *   **Specific Competing Products/Services:** List key overlapping offerings [SSX].
        *   **Recent Competitive Moves:** Describe significant strategic moves (e.g., mergers, acquisitions) with exact dates [SSX].
        *   **Analysis of Relative Positioning:** Compare key dimensions such as pricing, quality, innovation, etc., supported by data [SSX].
    *   ***Identify any strategic weaknesses relative to {company_name} and attribute them with inline citations [SSX].***

## 2. {company_name}'s Competitive Advantages & Positioning:
    *   Detail {company_name}'s key sources of sustainable competitive advantage (e.g., USP, technology, brand reputation) with specific examples and inline citations [SSX].
    *   Provide a balanced assessment of competitive strengths and weaknesses relative to identified competitors, citing all sources [SSX].

## 3. {company_name}'s Competitive Strategy:
    *   Describe the competitive strategy (e.g., cost leadership, differentiation) with explicit supporting statements and exact data where available [SSX].
    *   Identify and describe {company_name}'s primary value discipline (e.g., operational excellence, customer intimacy) with supporting evidence [SSX].
    *   List specific initiatives or investments aimed at enhancing its competitive position, including details like funding amount and timelines [SSX].
    *   Explain how {company_name} measures its competitive success (e.g., target market share, customer satisfaction metrics) with inline citations [SSX].

## 4. General Discussion:
    *   Provide a concluding single paragraph (300-500 words) that synthesizes the findings exclusively from Sections 1-3. Clearly link analytical statements using inline citations (e.g., "the market share data [SSX] indicates...").
    *   Structure the analysis logically by starting with an overall assessment, discussing strengths and weaknesses, and concluding with strategic takeaways for the Japanese audience.
    *   Do not introduce new factual claims that are not supported by previous sections.

Source and Accuracy Requirements:
*   **Accuracy:** All information must be factual and current. Specify currency, dates, and reporting periods.
*   **Traceability:** Every claim must include an inline citation [SSX] corresponding to a grounding URL in the final Sources list.
*   **Source Quality:** Use primarily official sources and reputable secondary sources only when necessary, with clear attribution.

{completion_instructions}
{FINAL_REVIEW_INSTRUCTION}
{final_source_instructions} 
{formatting_instructions}
""".strip()


def get_management_strategy_prompt(company_name: str, language: str = "Japanese"):
    """Generates a prompt for analyzing management strategy and mid-term business plan with all enhancements."""
    language_instruction = get_language_instruction(language)
    final_source_instructions = FINAL_SOURCE_LIST_INSTRUCTIONS_TEMPLATE.format(language=language)
    formatting_instructions = BASE_FORMATTING_INSTRUCTIONS.format(language=language)
    completion_instructions = COMPLETION_INSTRUCTION_TEMPLATE
    
    return f"""
Comprehensive Analysis of {company_name}'s Management Strategy and Mid-Term Business Plan: Focus, Execution, and Progress

Objective: To conduct an extensive analysis of **{company_name}**'s management strategy and mid-term business plan (MTP) by evaluating strategic pillars, execution effectiveness, progress against targets, and challenges. Focus on explaining why strategic choices were made and how progress is tracked using specific data with inline citations [SSX].

Target Audience Context: This analysis is designed for a **Japanese company** needing deep strategic insights. Present all information with exact dates, reporting periods, and clear official source attributions. {AUDIENCE_CONTEXT_REMINDER}

{language_instruction}

Research Requirements:
Conduct in-depth research from official sources (IR documents, Annual/Integrated Reports, earnings call transcripts, strategic website sections) ensuring all claims include inline citations [SSX] and specific dates or reporting periods. 
{HANDLING_MISSING_INFO_INSTRUCTION.format(language=language)}
{RESEARCH_DEPTH_INSTRUCTION}
{SPECIFICITY_INSTRUCTION}
{INLINE_CITATION_INSTRUCTION}
{ANALYSIS_SYNTHESIS_INSTRUCTION}

## 1. Management Strategy and Vision Alignment:
    *   Outline {company_name}'s overall management strategy and analyze its alignment with the company's long-term vision or purpose statement. Include precise references (e.g., "as of 2024-01-01") with inline citations [SSX].
    *   Explain the core management philosophy, values, and strategic approach with examples, including specific dates or document references [SSX].
    *   Identify key strategic pillars and priorities for the upcoming 3-5 years, explaining the rationale with numerical or qualitative evidence and inline citations [SSX].
    *   Describe any significant strategic shifts from previous plans, with supporting data and source references [SSX].

## 2. Current Mid-Term Business Plan (MTP) Overview:
    *   Identify the official name and exact time period of the current MTP (e.g., "FY2024-FY2026 MTP") with source references [SSX].
    *   Detail the main objectives and specific quantitative targets (financial and non-financial). Present these targets clearly (tables are acceptable) with explicit KPIs, currency, and target periods [SSX].
    *   Discuss key differences from previous strategic plans, supported by specific examples and inline citations [SSX].

## 3. Strategic Focus Areas and Initiatives:
    *   For each major strategic pillar identified:
        *   Detail the background and specific objectives of that area, explaining why it is a priority [SSX].
        *   Describe the relevant market conditions and industry trends influencing it, including specific figures or dates [SSX].
        *   List specific initiatives or projects (with funding details, timelines, and measurable outcomes) and explain how they support the pillar [SSX].
        *   Assess the potential impact and feasibility of these initiatives with supporting data [SSX].

## 4. Execution, Progress, and Adaptation:
    *   Identify key internal and external challenges affecting strategy execution, with precise examples and dates [SSX].
    *   Describe the specific countermeasures or adjustments stated by the company and assess their likely effectiveness [SSX].
    *   Provide the latest progress updates with detailed performance versus targets (using tables if necessary, with specified reporting periods and currency) [SSX].
    *   Highlight any strategic adjustments made in response to external events (e.g., economic shifts, regulatory changes), with inline citations [SSX].

## 5. General Discussion:
    *   Provide a single concluding paragraph (300-500 words) that synthesizes the findings from Sections 1-4. Clearly connect each analytical insight with inline citations (e.g., "the strategic shift noted in Section 1 [SSX] indicates...").
    *   Structure the discussion logically by starting with an overall assessment, discussing execution challenges, and concluding with strategic takeaways relevant for a Japanese audience.
    *   Do not introduce any new claims that are not derived from the previous sections.

Source and Accuracy Requirements:
*   **Accuracy:** Information must be factually correct. Specify currency and exact dates for all data.
*   **Traceability:** Every claim must have an inline citation [SSX] linked to the final Sources list.
*   **Source Quality:** Use primarily official company sources with clear and verifiable references.

{completion_instructions}
{FINAL_REVIEW_INSTRUCTION}
{final_source_instructions}
{formatting_instructions}
""".strip()


def get_regulatory_prompt(company_name: str, language: str = "Japanese"):
    """Generates a prompt for analyzing the regulatory environment for DX with all enhancements."""
    language_instruction = get_language_instruction(language)
    final_source_instructions = FINAL_SOURCE_LIST_INSTRUCTIONS_TEMPLATE.format(language=language)
    formatting_instructions = BASE_FORMATTING_INSTRUCTIONS.format(language=language)
    completion_instructions = COMPLETION_INSTRUCTION_TEMPLATE
    
    return f'''
In-Depth Analysis of the Regulatory Environment and Compliance for {company_name}'s Digital Transformation (DX)

Objective: To analyze the regulatory environment impacting **{company_name}**'s DX initiatives, including data privacy, cybersecurity, AI governance, and sector-specific digital rules. Evaluate the company's compliance approaches and any enforcement actions with precise dates and references [SSX].

Target Audience Context: The output is for a **Japanese company** reviewing regulatory risks for potential partnership, investment, or competitive evaluation. Provide exact dates, reporting periods, and detailed official source references [SSX]. {AUDIENCE_CONTEXT_REMINDER}

{language_instruction}

Research Requirements:
Conduct deep research on {company_name}'s regulatory environment using official documents and reputable publications. Each claim must be supported by an inline citation [SSX] with specific dates or reporting periods.
{HANDLING_MISSING_INFO_INSTRUCTION.format(language=language)}
{RESEARCH_DEPTH_INSTRUCTION}
{SPECIFICITY_INSTRUCTION}
{INLINE_CITATION_INSTRUCTION}
{ANALYSIS_SYNTHESIS_INSTRUCTION}

## 1. Regulatory Environment and Compliance:
    *   Describe the key regulatory policies impacting {company_name}'s DX. Identify applicable data privacy laws (e.g., GDPR, APPI) with specific references and dates [SSX].
    *   Explain cybersecurity mandates and relevant standards (e.g., NIS2 Directive) with precise source details [SSX].
    *   Discuss emerging AI governance regulations (e.g., EU AI Act) and any sector-specific digital rules, citing official documents [SSX].
    *   Explain how these regulations influence {company_name}'s strategic choices (e.g., data handling, cybersecurity investments) with exact examples and dates [SSX].
    *   Detail {company_name}'s stated compliance approach, including policies, certifications (e.g., ISO 27001), and integration of compliance in DX project planning [SSX].
    *   Identify any significant regulatory enforcement actions or controversies in the last 3-5 years, specifying dates, regulatory bodies, outcomes (with currency where applicable), and company responses [SSX].

## 2. General Discussion:
    *   Provide a concluding single paragraph (300-500 words) that synthesizes the regulatory findings exclusively from Section 1. Clearly articulate the regulatory impacts and compliance posture with inline citations [SSX].
    *   Structure the analysis by summarizing the regulatory environment, assessing compliance strengths and weaknesses, and concluding with an evaluation of risk tailored to a Japanese audience.
    *   Do not introduce new factual claims beyond the provided analysis.

Source and Accuracy Requirements:
*   **Accuracy:** All regulatory details must be current and verifiable. Include specific dates and currency information as applicable.
*   **Traceability:** Each statement must have an inline citation [SSX] corresponding to the final Sources list.
*   **Source Quality:** Use official company disclosures, government publications, and reputable news sources with clear references.

{completion_instructions}
{FINAL_REVIEW_INSTRUCTION}
{final_source_instructions}
{formatting_instructions}
'''.strip()


def get_crisis_prompt(company_name: str, language: str = "Japanese"):
    """Generates a prompt for analyzing digital crisis management and business continuity with all enhancements."""
    language_instruction = get_language_instruction(language)
    final_source_instructions = FINAL_SOURCE_LIST_INSTRUCTIONS_TEMPLATE.format(language=language)
    formatting_instructions = BASE_FORMATTING_INSTRUCTIONS.format(language=language)
    completion_instructions = COMPLETION_INSTRUCTION_TEMPLATE
    
    return f'''
In-Depth Analysis of {company_name}'s Digital Crisis Management and Business Continuity

Objective: To analyze how **{company_name}** prepares for and manages digital crises (e.g., cyberattacks, system outages) and its business continuity plans. Include details on past incidents with exact dates, impacts (including financial figures with specified currency), and the company's response strategies, all supported by inline citations [SSX].

Target Audience Context: This output is for a **Japanese company** assessing digital risk resilience for strategic decision-making. Provide precise data (with dates and reporting periods) and official source references [SSX]. {AUDIENCE_CONTEXT_REMINDER}

{language_instruction}

Research Requirements:
Conduct thorough research on {company_name}'s crisis management and business continuity from official disclosures and reputable reports. Include inline citations [SSX] for every fact, with specific dates or periods.
{HANDLING_MISSING_INFO_INSTRUCTION.format(language=language)}
{RESEARCH_DEPTH_INSTRUCTION}
{SPECIFICITY_INSTRUCTION}
{INLINE_CITATION_INSTRUCTION}
{ANALYSIS_SYNTHESIS_INSTRUCTION}

## 1. Crisis Management and Business Continuity:
    *   **Handling of Past Digital Crises (Last 5 Years):** Describe significant publicly reported digital crises (e.g., ransomware attacks, data breaches, prolonged outages) with approximate dates, impact details (systems affected, data compromised, financial loss in specified currency), and sources [SSX].
    *   Detail the company's public response and subsequent actions (e.g., remedial measures, regulatory reporting, support for affected parties), including any lessons learned, with inline citations [SSX].
    *   Explain the stated approach to digital crisis management (e.g., existence of an Incident Response Plan or dedicated crisis teams) and business continuity planning (e.g., recovery time objectives), citing precise official sources and dates [SSX].
    *   Describe roles or governance structures involved in managing digital crises, supported by verifiable details [SSX].

## 2. General Discussion:
    *   Provide a concluding single paragraph (300-500 words) synthesizing the findings from Section 1. Clearly explain how {company_name}'s crisis management practices and business continuity plans contribute to overall resilience, using inline citations (e.g., "the early response [SSX] demonstrates...").
    *   Structure the discussion logically, starting with a summary of past incidents, followed by evaluation of the response and preparedness, and concluding with strengths, weaknesses, and recommendations relevant to a Japanese audience.
    *   Do not introduce any new claims not supported by the previous analysis.

Source and Accuracy Requirements:
*   **Accuracy:** All incident details and response measures must be current, with currency and exact dates specified.
*   **Traceability:** Every claim must include an inline citation [SSX] linked to a source in the final Sources list.
*   **Source Quality:** Prioritize official company disclosures and reputable news or cybersecurity firm reports.

{completion_instructions}
{FINAL_REVIEW_INSTRUCTION}
{final_source_instructions}
{formatting_instructions}
'''.strip()


def get_digital_transformation_prompt(company_name: str, language: str = "Japanese"):
    """Generates a prompt for analyzing DX strategy and execution with all enhancements."""
    language_instruction = get_language_instruction(language)
    final_source_instructions = FINAL_SOURCE_LIST_INSTRUCTIONS_TEMPLATE.format(language=language)
    formatting_instructions = BASE_FORMATTING_INSTRUCTIONS.format(language=language)
    completion_instructions = COMPLETION_INSTRUCTION_TEMPLATE
    
    return f"""
In-Depth Analysis of {company_name}'s Digital Transformation (DX) Strategy and Execution

Objective: To analyze {company_name}'s Digital Transformation strategy, including its vision, key priorities, major investments, and specific case studies of successful digital initiatives. Evaluate also how DX integrates compliance and crisis management. Use precise data (e.g., specific investment amounts, dates) supported by inline citations [SSX].

Target Audience Context: The analysis is prepared for a **Japanese company**; therefore, it must be detailed, with exact figures (specifying currency and reporting periods) and official source references. {AUDIENCE_CONTEXT_REMINDER}

{language_instruction}

Research Requirements:
Conduct detailed research on {company_name}'s DX journey using official sources (company reports, dedicated DX documentation, press releases) and reputable analyses. Every claim, financial figure, and example must include an inline citation [SSX] and specific dates or periods.
{HANDLING_MISSING_INFO_INSTRUCTION.format(language=language)}
{RESEARCH_DEPTH_INSTRUCTION}
{SPECIFICITY_INSTRUCTION}
{INLINE_CITATION_INSTRUCTION}
{ANALYSIS_SYNTHESIS_INSTRUCTION}

## 1. DX Strategy Overview:
    *   Outline {company_name}'s overall digital transformation vision and strategic goals (e.g., to enhance customer experience, improve efficiency) with precise references and inline citations [SSX].
    *   Identify the key strategic priorities or pillars of the DX strategy with specific details and dates [SSX].
    *   List major DX initiatives or projects currently underway or recently completed, including specific objectives and target outcomes [SSX].

## 2. DX Investments Analysis (Last 3 Fiscal Years):
    *   Analyze {company_name}'s investments in DX by providing detailed breakdowns by initiative or area (e.g., cloud infrastructure, AI development) in a table format. Include specific investment amounts, funding sources, timelines, and reporting periods with inline citations [SSX].
    *   Describe overall investment trends over the last 3 years (e.g., increasing, stable) with supporting data [SSX].

## 3. DX Case Studies & Implementation Examples:
    *   Provide detailed descriptions of 2-3 specific DX implementation examples or case studies. For each example, describe:
        *   The technology or initiative implemented.
        *   The business objective and measurable outcomes (e.g., cost savings percentage, efficiency gains, new revenue in specified currency) with exact data and sources [SSX].
        *   Explain why this example was highlighted by the company (e.g., flagship project) with inline citations [SSX].

## 4. Regulatory Environment, Compliance, and Crisis Management (Related to DX):
    *   Briefly summarize the regulatory trends that impact DX (e.g., data privacy, cybersecurity) with specific laws and exact dates [SSX].
    *   Describe how {company_name} integrates compliance (e.g., certifications, privacy-by-design) into its DX efforts with precise source details [SSX].
    *   Mention how crisis management and business continuity considerations are addressed in the context of DX, citing official examples where available [SSX].

## 5. General Discussion:
    *   Provide a concluding single paragraph (300-500 words) that synthesizes the findings from Sections 1-4. Explicitly link data points and examples using inline citations (e.g., "the investment increase [SSX] supports the strategic shift...").
    *   Structure your discussion logically—start with the DX strategy, proceed through investment and implementation details, then integrate regulatory and risk management aspects.
    *   Tailor your final analysis for a Japanese audience. Do not introduce new facts outside of the presented analysis.

Source and Accuracy Requirements:
*   **Accuracy:** All data must be current and verified. Specify currency and reporting period for every monetary value.
*   **Traceability:** Every fact must include an inline citation [SSX] that corresponds to a source in the final Sources list.
*   **Source Quality:** Prioritize official company disclosures and reputable research with clear source details.

{completion_instructions}
{FINAL_REVIEW_INSTRUCTION}
{final_source_instructions}
{formatting_instructions}
""".strip()


def get_business_structure_prompt(company_name: str, language: str = "Japanese"):
    """Generates a prompt for analyzing business structure, geographic footprint, ownership, and leadership linkages with all enhancements."""
    language_instruction = get_language_instruction(language)
    final_source_instructions = FINAL_SOURCE_LIST_INSTRUCTIONS_TEMPLATE.format(language=language)
    formatting_instructions = BASE_FORMATTING_INSTRUCTIONS.format(language=language)
    completion_instructions = COMPLETION_INSTRUCTION_TEMPLATE
    
    business_structure_completion_guidance = textwrap.dedent(f"""\
    **Critical Completeness Requirements:**
    
    *   **Priority Information:** If time or data are limited, prioritize completing:
        1. The business segment breakdown with at least the most recent fiscal year data
        2. The geographic segment breakdown with at least the most recent fiscal year data
        3. The top 3-5 major shareholders
        
    *   **Progressive Completion:** For each section, provide at least basic information before attempting more detailed analysis:
        * For segments: At minimum, list main segments and their % of revenue for the most recent year
        * For geography: At minimum, list main regions and their % of revenue for the most recent year
        * For shareholders: At minimum, list the largest institutional/individual shareholders
        
    *   **Partial Data Handling:** If 3-year data is unavailable, clearly state the available timeframe (e.g., "Data available for FY2022-2023 only [SSX]") and proceed with analysis of available data rather than omitting the entire section.
    
    *   **Final Verification:** Before completing each section, verify:
        * All priority information points are addressed
        * At least one full fiscal year of data is provided for segments
        * All available ownership information is included
        * Each data point includes proper inline citation [SSX]
    """)
    
    return f"""
In-Depth Analysis of {company_name}'s Business Structure, Geographic Footprint, Ownership, and Strategic Vision Linkages

Objective: To analytically review {company_name}'s operational structure, geographic markets, ownership composition, and how these link to leadership's strategic vision. Include specific figures (with currency and fiscal year), and reference official sources (e.g., Annual Report, IR materials) with inline citations [SSX].

Target Audience Context: This output is intended for a **Japanese company** performing market analysis and partnership evaluation. Present all claims with exact dates, detailed quantitative figures, and clear source references [SSX]. {AUDIENCE_CONTEXT_REMINDER}

{language_instruction}

Research Requirements:
Perform a critical analysis using official sources (Annual/Integrated Reports, IR materials, filings, corporate governance documents). Supplement with reputable secondary sources only when necessary, ensuring each claim includes an inline citation [SSX] and precise data (e.g., "as of YYYY-MM-DD").
{HANDLING_MISSING_INFO_INSTRUCTION.format(language=language)}
{RESEARCH_DEPTH_INSTRUCTION}
{SPECIFICITY_INSTRUCTION}
{INLINE_CITATION_INSTRUCTION}
{ANALYSIS_SYNTHESIS_INSTRUCTION}
{business_structure_completion_guidance}

## 1. Business Segment Analysis (Last 3 Fiscal Years):
    *   List the reported business segments (or main business lines) using official descriptions. Include a table with consolidated sales figures (specify currency and fiscal year) and composition ratios, with each data point referenced [SSX].
    *   For each segment, provide:
        * Official segment name as reported by the company [SSX]
        * Brief description of products/services in that segment (1-2 sentences) [SSX]
        * Revenue figures (with currency and fiscal year) for the last 3 years or maximum available [SSX]
        * Year-over-year growth/decline rates (%) with specific calculations [SSX]
        * Profit margins (if available) with exact reporting period [SSX]
    *   Analyze significant trends (e.g., growth/decline, margin changes) with specific percentages and dates [SSX].
    *   Identify the fastest growing and most profitable segments with supporting data [SSX].

## 2. Geographic Segment Analysis (Last 3 Fiscal Years):
    *   List the geographic regions or segments with corresponding sales figures and composition ratios in a table, including the fiscal year and currency [SSX].
    *   For each geographic region, provide:
        * Region name as officially reported by the company [SSX]
        * Revenue figures (with currency and fiscal year) for last 3 years or maximum available [SSX]
        * Year-over-year growth/decline rates (%) with specific calculations [SSX]
        * Percentage of total revenue for each year reported [SSX]
    *   Analyze regional trends with specific supporting data and inline citations [SSX].
    *   Identify key growth markets and declining markets with specific figures [SSX].
    *   Note any stated plans for geographic expansion or contraction with dates and details [SSX].

## 3. Major Shareholders & Ownership Structure:
    *   Describe the overall ownership type (e.g., publicly traded, privately held) with specific details [SSX].
    *   List the top 5-10 major shareholders with:
        * Exact shareholder names as officially reported [SSX]
        * Precise ownership percentages (as of the most recent reporting date) [SSX]
        * Shareholder type (institutional, individual, government, etc.) [SSX]
        * Any changes in major shareholders over the past year, if reported [SSX]
    *   Include information on:
        * Total shares outstanding (with exact as-of date) [SSX]
        * Free float percentage (if available) [SSX]
        * Presence of controlling shareholders or parent companies [SSX]
        * Cross-shareholdings with business partners (if applicable) [SSX]
    *   Include any details regarding different classes of shares, if applicable, and provide an analytical comment on ownership concentration [SSX].

## 4. Corporate Group Structure:
    *   Describe the parent-subsidiary relationships and overall corporate group structure [SSX].
    *   List key subsidiaries with:
        * Official subsidiary names [SSX]
        * Ownership percentage by the parent company [SSX]
        * Primary business functions of each subsidiary [SSX]
        * Country/region of incorporation [SSX]
    *   Note any recent restructuring, mergers, or acquisitions with specific dates and transaction details (if available) [SSX].

## 5. Leadership Strategic Outlook & Vision (Verbatim Quotes - Linkages):
    *   Provide verbatim quotes from key executives (CEO, Chairman, and optionally CFO/CSO) that address:
        * Long-term strategic vision for the company structure [SSX]
        * Plans for business segment growth/rationalization [SSX]
        * Geographic expansion or focus strategies [SSX]
        * Comments on ownership structure or major shareholder relations (if any) [SSX]
    *   Each quote must have its source cited immediately after it (e.g., "(Source: Annual Report 2023, p. 5)") and must be linked to relevant findings in previous sections with inline citations [SSX].
    *   Where possible, explicitly connect a quote to a specific finding in Sections 1-4 (e.g., "Reflecting the focus on Asia in Section 2, the CEO stated... [SSX]").

## 6. General Discussion:
    *   Provide a single concluding paragraph (300-500 words) synthesizing the findings from Sections 1-5. Clearly link analytical insights and comparisons using inline citations (e.g., "the shift in segment sales [SSX] suggests...").
    *   Address specifically:
        * The alignment between business structure and stated strategic vision [SSX]
        * How ownership structure may influence business decisions [SSX]
        * Geographic expansion strategies and their business segment implications [SSX]
        * Potential future developments based on current structure and leadership comments [SSX]
    *   Structure your discussion logically, starting with a summary of business and geographic drivers, assessing ownership influence and leadership vision, and concluding with strategic implications for a Japanese audience.
    *   Do not introduce new unsupported claims.

Source and Accuracy Requirements:
*   **Accuracy:** Ensure all data is precise, with currency and fiscal year reported for numerical values.
*   **Traceability:** Every fact must include an inline citation [SSX] corresponding to the final Sources list.
*   **Source Quality:** Use only primary official sources with clear documentation.

{completion_instructions}
{FINAL_REVIEW_INSTRUCTION}
{final_source_instructions}
{formatting_instructions}
""".strip()


def get_vision_prompt(company_name: str, language: str = "Japanese"):
    """Generates a prompt focused on company vision and strategic purpose with all enhancements."""
    language_instruction = get_language_instruction(language)
    final_source_instructions = FINAL_SOURCE_LIST_INSTRUCTIONS_TEMPLATE.format(language=language)
    formatting_instructions = BASE_FORMATTING_INSTRUCTIONS.format(language=language)
    completion_instructions = COMPLETION_INSTRUCTION_TEMPLATE
    
    return f"""
Analysis of {company_name}'s Strategic Vision and Purpose

Objective: To provide a detailed analysis of {company_name}'s officially stated vision, mission, or purpose. Break down its core components (pillars, strategic themes), explain how progress is measured using specific KPIs, and assess stakeholder focus. Include exact quotes, dates, and reference all information using inline citations [SSX].

Target Audience Context: This analysis is for a **Japanese company** assessing strategic alignment and direction. Present precise information with clear source references and detailed explanations (e.g., "as per the Annual Report 2023, p.12, [SSX]") {AUDIENCE_CONTEXT_REMINDER}

{language_instruction}

Research Requirements:
Conduct in-depth research using official sources such as the company website (strategy, about us, IR, sustainability pages), Annual/Integrated Reports, MTP documents, and press releases. Every claim or data point must have an inline citation [SSX] and include specific dates or periods.
{HANDLING_MISSING_INFO_INSTRUCTION.format(language=language)}
{RESEARCH_DEPTH_INSTRUCTION}
{SPECIFICITY_INSTRUCTION}
{INLINE_CITATION_INSTRUCTION}
{ANALYSIS_SYNTHESIS_INSTRUCTION}

## 1. Company Vision and Strategy Elements:
    *   **Vision/Purpose/Mission Statement:** Present {company_name}'s official statement verbatim with an inline citation [SSX] and explain its core message.
    *   **Strategic Vision Components/Pillars:** List and explain the key strategic themes that underpin the vision, with definitions provided on first use and precise source references [SSX].
    *   **Vision Measures / KPIs:** Identify the specific measures or KPIs used to track progress towards the vision. Present these in a table if needed, including currency (if applicable) and reporting periods, with inline citations [SSX].
    *   ***Stakeholder Focus:*** Analyze how the vision addresses key stakeholder groups (e.g., customers, employees, investors) with supporting evidence and citations [SSX].

## 2. General Discussion:
    *   Provide a concluding single paragraph (300-500 words) synthesizing the information in Section 1. Explain the clarity, ambition, and internal coherence of the vision with explicit connections using inline citations (e.g., "the KPI alignment [SSX] confirms...").
    *   Structure the analysis logically—starting with an overall summary, then detailing components, and finally evaluating strategic relevance for a Japanese audience.
    *   Do not introduce new claims beyond the synthesized findings.

Source and Accuracy Requirements:
*   **Accuracy:** Ensure all statements are current and verified. Specify currency for financial KPIs.
*   **Traceability:** Every claim must have an inline citation [SSX] that corresponds to a source in the final Sources list.
*   **Source Quality:** Use primarily official company documents and well-documented releases.

{completion_instructions}
{FINAL_REVIEW_INSTRUCTION}
{final_source_instructions}
{formatting_instructions}
""".strip()


def get_management_message_prompt(company_name: str, language: str = "Japanese"):
    """Generates a prompt for collecting strategic quotes from leadership with all enhancements."""
    language_instruction = get_language_instruction(language)
    final_source_instructions = FINAL_SOURCE_LIST_INSTRUCTIONS_TEMPLATE.format(language=language)
    formatting_instructions = BASE_FORMATTING_INSTRUCTIONS.format(language=language)
    completion_instructions = COMPLETION_INSTRUCTION_TEMPLATE
    
    return f"""
Detailed Leadership Strategic Outlook (Verbatim Quotes) for {company_name}

Objective: To compile a collection of direct, verbatim strategic quotes from {company_name}'s senior leadership (CEO, Chairman, and optionally CFO/CSO) that illustrate the company's strategic direction, future plans, and responses to challenges. Each quote must be accurately transcribed with an immediate source citation in parentheses and an inline citation [SSX] if it supports further analytical claims.

Target Audience Context: This information is for a **Japanese company** that requires a clear understanding of leadership's strategic communication. Ensure that every quote includes exact dates and precise source references [SSX]. {AUDIENCE_CONTEXT_REMINDER}

{language_instruction}

Research Requirements:
Conduct focused research on official communications (e.g., Earnings Call Transcripts, Annual Reports, Investor Day presentations) to extract strategically relevant verbatim quotes. Each quote must have an inline citation [SSX] and be followed by its specific source reference in parentheses (e.g., "(Source: Annual Report 2023, p.5)").
{HANDLING_MISSING_INFO_INSTRUCTION.format(language=language)}
{RESEARCH_DEPTH_INSTRUCTION}
{SPECIFICITY_INSTRUCTION}
{INLINE_CITATION_INSTRUCTION}
{ANALYSIS_SYNTHESIS_INSTRUCTION}

## 1. Leadership Strategic Outlook (Verbatim Quotes):

### [CEO Name], CEO (Specify Name)
*   Provide a brief 1-2 sentence summary of the key strategic themes reflected in the CEO's quotes (include the date range, e.g., 2023-2024) with inline citation [SSX].
*   **Quote 1:** "..." (Source: Specify source with exact date and page; include inline citation [SSX])
*   **Quote 2:** "..." (Source: Specify source with exact date and page; include inline citation [SSX])
*   **Quote 3:** "..." (Source: Specify source; include inline citation [SSX])
*   **Quote 4:** "..." (Source: Specify source; include inline citation [SSX])

### [Chairman Name], Chairman (if distinct)
*   Provide a summary of key themes in the Chairman's quotes (include date range) with inline citation [SSX].
*   **Quote 1:** "..." (Source: Specify source; include inline citation [SSX])
*   **Quote 2:** "..." (Source: Specify source; include inline citation [SSX])
*   **Quote 3:** "..." (Source: Specify source; include inline citation [SSX])

### [Other Key Executive Name], [Title] (Optional if relevant)
*   Provide a brief summary of their strategic focus (include date range) with inline citation [SSX].
*   **Quote 1:** "..." (Source: Specify source; include inline citation [SSX])
*   **Quote 2:** "..." (Source: Specify source; include inline citation [SSX])

## 2. General Discussion:
    *   Provide a concluding single paragraph (300-500 words) synthesizing the key strategic messages from the collected quotes. Explicitly link recurring themes using inline citations (e.g., "the emphasis on digital innovation [SSX] indicates...").
    *   Structure your analysis logically and tailor the insights for the Japanese audience.
    *   Do not introduce any new factual claims that are not derived from the quotes.

Source and Accuracy Requirements:
*   **Accuracy:** Every quote must be verbatim with correct speaker roles and dates.
*   **Traceability:** Each quote must include an inline citation [SSX] corresponding to the final Sources list.
*   **Source Quality:** Use official communications only, with clear and verifiable details.

{completion_instructions}
{FINAL_REVIEW_INSTRUCTION}
{final_source_instructions}
{formatting_instructions}
""".strip()


def get_strategy_research_prompt(company_name: str, target_company: str, language: str = "Japanese"):
    """
    Generates a prompt for creating a comprehensive 3-year Strategy Research Action Plan
    specifically for {target_company}, leveraging {company_name}'s official context and capabilities.
    The plan uses verifiable data from Gemini (and {company_name}'s knowledge) to craft a highly
    targeted approach, maintaining single-entity coverage. All factual claims must have an
    inline citation [SSX].
    """
    language_instruction = get_language_instruction(language)
    final_source_instructions = FINAL_SOURCE_LIST_INSTRUCTIONS_TEMPLATE.format(language=language)
    formatting_instructions = BASE_FORMATTING_INSTRUCTIONS.format(language=language)
    completion_instructions = COMPLETION_INSTRUCTION_TEMPLATE

    return f"""
Comprehensive 3-Year Strategy Research Action Plan for {target_company} ({company_name} Specialist Approach)

Objective: Create a highly detailed, data-driven strategy research for the next three fiscal years, using {company_name}'s official solutions and insight. This plan must align with the verified data from Gemini and {company_name}'s public resources, focusing on a single entity. Avoid generic or unsupported content.

Target Audience Context: This plan is developed for {company_name}. All recommendations should reflect how {company_name} can best serve {target_company}, referencing real {company_name} offerings, known solution strengths, and verifiable data. {AUDIENCE_CONTEXT_REMINDER}

{language_instruction}

Research Requirements:
*   Use only data validated through Gemini or official {company_name} sources.
*   Each fact or figure must be backed by an inline citation [SSX]. Omit any unverified points.
*   If employee figures appear, provide a range (e.g., 5,000–8,000 employees) if that is how data is presented.
*   Incorporate {company_name}'s known core competencies (managed services, network security, cloud integration, etc.) where relevant.

{HANDLING_MISSING_INFO_INSTRUCTION.format(language=language)}
{RESEARCH_DEPTH_INSTRUCTION}
{SPECIFICITY_INSTRUCTION}
{INLINE_CITATION_INSTRUCTION}
{ANALYSIS_SYNTHESIS_INSTRUCTION}
{ADDITIONAL_REFINED_INSTRUCTIONS}

## 1. Customer Profile (Incorporating {company_name} Context)
    *   Summarize {target_company}'s business scope, HQ location, current CEO, and approximate employee range [SSX].
    *   Reference any official {company_name} insights—e.g., prior dealings, industry commentary, or synergy points—if verifiable [SSX].

## 2. Revenue Analysis & Growth Drivers
    *   Extract revenue for FY2021, FY2022, and FY2023 if available [SSX].
    *   Calculate YoY growth rates; identify segments/units fueling increases or declines [SSX].
    *   Discuss how {company_name} solutions can reinforce high-growth areas or address weaknesses [SSX].

## 3. Financial Performance Indicators
    *   Briefly outline net income trends for 3 years [SSX].
    *   Note profitable divisions/BU and potential {company_name} alignments [SSX].
    *   Use any margin/benchmark data to contextualize {company_name}'s opportunity [SSX].

## 4. Strategic Initiatives & Key {company_name} Alignments
    *   List {target_company}'s stated initiatives (investment amounts, timeline, technology focus) [SSX].
    *   Match each initiative to a specific {company_name} solution (e.g., network modernization, security platforms) [SSX].
    *   Emphasize the direct synergy between the initiative and a known {company_name} capability.

## 5. Decision-Making Structure & Stakeholders
    *   Outline the org chart focusing on IT budget owners or transformation leads [SSX].
    *   Note any historical {company_name}–{target_company} interactions if grounded [SSX].

## 6. Critical Business Challenges & {company_name} Solutions
    *   Enumerate {target_company}'s major challenges (operational, tech, strategic) [SSX].
    *   Propose definitive {company_name} solutions for each challenge, clarifying exactly how they resolve the issue [SSX].
    *   Avoid vague language; specify outcomes, timelines, or metrics where possible.

## 7. Technology Roadmap with {company_name} Capabilities
    *   Present {target_company}'s 3-year tech roadmap gleaned from data [SSX].
    *   Show how {company_name}'s offerings (e.g., managed infrastructure, AI/IoT, cloud security) tie into that roadmap [SSX].

## 8. Engagement Strategy (FY2025–2027)
    *   Provide a quarter-by-quarter plan:
        - {company_name} solutions proposed
        - Target internal department/unit
        - Direct need from {target_company}'s data
        - Projected order values or spending estimates (if verifiable) [SSX]
    *   No generic proposals—reference official challenges or initiatives [SSX].

## 9. Competitive Positioning
    *   Identify existing IT or communications vendors/partners per available data [SSX].
    *   Highlight {company_name}'s specific differentiators (technical, cost, brand, synergy) against each competitor [SSX].

## 10. Success Metrics & "Expected 2025 Results"
    *   Provide specific, measurable goals (e.g., "Close two major deals per quarter [SSX]").
    *   Include a short table or bullet list with metric definitions, referencing relevant baseline data [SSX].
    *   Label them "Expected 2025 Results" or "Projected KPIs," and explain the calculation rationale (e.g., prior {company_name} engagement patterns, external benchmarks) [SSX].

## 11. Final 3-Year Strategy Research Summary
    *   Conclude with a single paragraph (~300–500 words) integrating all insights. Demonstrate how {company_name}'s approach directly tackles {target_company}'s environment and fosters mutual growth [SSX].
    *   Do not introduce new data; only synthesize prior points.

Source and Accuracy Requirements:
*   **Accuracy:** All data or solution references must be grounded in official records or valid {company_name}/Gemini insight.  
*   **Traceability:** Each fact or figure includes [SSX], linking to final source(s).  
*   **Single-Entity Coverage:** Strictly reference {target_company}'s data; omit any similarly named entities.

{completion_instructions}
{FINAL_REVIEW_INSTRUCTION}
{final_source_instructions}
{formatting_instructions}
""".strip()

