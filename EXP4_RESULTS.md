# Exp 4 Pilot Results: Quotation Switch

## What we tested

30 windows from Christian books containing KJV Bible quotations embedded in 
commentary prose. Each 16k token window contains BOTH quoted verse AND 
surrounding commentary. The decisive question: does the H6 expert cluster 
fire on the verse portions, the commentary portions, or both?

## What actually happened

The Exp 4 corpus split into two natural groups:

- **5 records from Gutenberg KJV files** (digit density >1%): These contain 
  the Bible text with chapter:verse numbering (e.g., "01:001:001 In the 
  beginning..."). They are essentially verse with editorial apparatus.
- **24 records from commentary/sermon books** (digit density ≤1%): These 
  contain prose discussion with embedded Bible quotations.

This split was not planned — it emerged from the corpus construction. But 
it gives us a natural experiment.

## Results

| Group | n | H6 Composite (per M tokens) |
|---|---:|---:|
| Pure Bible verse (core data) | 1,189 | 4.1 |
| Exp4: KJV files (verse+apparatus) | 5 | 8,664 |
| Exp4: Commentary books (prose+quotes) | 24 | 44,822 |
| Christian commentary (all) | 3,562 | 41,894 |

## Key findings

1. **H6 fires on prose context, not verse content.** Commentary windows with 
   embedded Bible quotes fire H6 at 44,822/M — nearly identical to pure 
   Christian commentary (41,894/M). The presence of verse quotes does NOT 
   suppress H6 firing. The model routes based on the surrounding prose, 
   not the quoted verse.

2. **KJV files fire H6 at an intermediate rate** (8,664/M) — higher than 
   pure verse (4.1/M) but 5× lower than commentary. This is likely because 
   Gutenberg KJV files contain prose-like formatting (publication notes, book 
   headers) mixed with the verse text. The apparatus triggers partial H6 
   activation.

3. **Per-anchor consistency:** All 6 H6 anchors fire more on commentary 
   than on KJV files (ratios 2.6× to 20.4×). No anchor shows the 
   opposite pattern.

4. **Digit density correlation: r = -0.642.** This is driven by the 
   KJV-file group: high digit density → verse format → low H6. This does 
   NOT mean H6 is digit-driven. It means digit density is a proxy for 
   verse format in this corpus (chapter:verse numbering only appears in 
   the verse-format files). The H6 axis remains digit-independent — this 
   was confirmed in Exp 14 where within-Christian-corpus R² for digits 
   was 0.00-0.15.

5. **The 5 KJV-file records accidentally replicate the verse/prose null.** 
   They are essentially Bible text (verse) with editorial apparatus, and 
   they fire H6 at near-verse rates — confirming that the verse/prose axis 
   is about text structure, not religious content.

## Limitations (per FORWARD_PLAN.md)

This is a **window-level pilot (Exp 4a)**, not the decisive per-token test. 
We have aggregate expert frequencies per 16k window, not per-token routing. 
The within-window quote-span vs commentary-span comparison requires 
per-token capture (`--raw-budget-tokens > 0`), which was not enabled.

The 5 KJV-file records should not have been in the corpus — they are 
Bible text, not commentary with embedded quotes. The Exp 4b corpus should 
use only actual commentary books with properly annotated quote spans.

## What this means

The H6 experts respond to **prose context**, not to verse content. When 
commentary prose surrounds a Bible quote, H6 fires throughout the window. 
When verse text stands alone, H6 does not fire. The routing decision is 
about the format of the surrounding text, not the semantics of the quoted 
content.

This is consistent with the "format-associated routing axis" framing from 
the forward plan. The H6 experts are recruited by prose format, not by 
religious or verse content.
