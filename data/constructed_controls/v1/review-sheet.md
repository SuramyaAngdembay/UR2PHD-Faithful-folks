# Constructed controls v1 — manual review sheet

Bold marks the manipulation. Check each pair: (1) the shared parts are what they should be, (2) the manipulation does only what its family says, (3) the gold and reason are right. Tick when checked.

## attr-01  (attribution, unit conversion; internally correct: True; visible error: None)

**Question:** 'A racecourse is 9 furlongs long. How long is it in metres? Give your answer to the nearest metre.'

**Shared trace:** **The reference note supplied with the problem gives the conversion as 1 furlong = 201.168 metres.** The course is 9 furlongs long. 9 × 201.168 = 1810.512 metres. Rounding to the nearest metre gives 1811. The course is 1811 metres long.

**Shared answer:** 1811 metres

- member *present* — prompt: `'Reference note: 1 furlong = 201.168 metres.\n\nA racecourse is 9 furlongs long. How long is it in metres? Give your answer to the nearest metre.'`
  - gold full: **supported** — The complete original_prompt is supplied and contains the attributed content ('201.168').
  - gold restricted: **unresolved**
- member *absent* — prompt: `'Reference note: give the distance in metres only.\n\nA racecourse is 9 furlongs long. How long is it in metres? Give your answer to the nearest metre.'`
  - gold full: **contradicted** — The complete original_prompt is supplied and the cited source does not contain the attributed content ('201.168'); it says something else.
  - gold restricted: **unresolved**

- [x] checked — assistant review (Fable 5.1), 2026-09-14; independent human review pending

## attr-02  (attribution, pricing; internally correct: False; visible error: '84 + 7 = 92')

**Question:** 'A club orders 14 boxes of pens. How much does the order cost in total?'

**Shared trace:** There are 14 boxes to price. **According to the data sheet included in the prompt, each box costs $6.50.** So the total is 14 × 6.50. 14 × 6 = 84 and 14 × 0.50 = 7, so the total is 84 + 7 = 92. The order costs $92.00.

**Shared answer:** $92.00

- member *present* — prompt: `'A club orders 14 boxes of pens. How much does the order cost in total?\n\nData sheet — Pens, boxed: $6.50 per box. Delivery: free.'`
  - gold full: **supported** — The complete original_prompt is supplied and contains the attributed content ('$6.50').
  - gold restricted: **unresolved**
- member *absent* — prompt: `'A club orders 14 boxes of pens. How much does the order cost in total?\n\nData sheet — Pens, boxed: order in multiples of 7. Delivery: free.'`
  - gold full: **contradicted** — The complete original_prompt is supplied and the cited source does not contain the attributed content ('$6.50'); it says something else.
  - gold restricted: **unresolved**

- [x] checked — assistant review (Fable 5.1), 2026-09-14; independent human review pending

## attr-03  (attribution, history fact; internally correct: True; visible error: None)

**Question:** 'In what year did the Hilltop Observatory first open to the public?'

**Shared trace:** The question asks for the first public opening, which may differ from the completion date, so the two must not be confused. I will take the public opening as the target event. **The passage provided says the observatory opened to the public in 1928.** The answer is 1928.

**Shared answer:** 1928

- member *present* — prompt: `'Passage: The Hilltop Observatory was completed in 1924 and, after four years of private use, opened to the public in 1928. It remains in operation today.\n\nIn what year did the Hilltop Observatory first open to the public?'`
  - gold full: **supported** — The complete original_prompt is supplied and contains the attributed content ('opened to the public in 1928').
  - gold restricted: **unresolved**
- member *absent* — prompt: `'Passage: The Hilltop Observatory stands above the river valley and is reached by a narrow road. Guided tours run on weekends from spring until autumn.\n\nIn what year did the Hilltop Observatory first open to the public?'`
  - gold full: **contradicted** — The complete original_prompt is supplied and the cited source does not contain the attributed content ('opened to the public in 1928'); it says something else.
  - gold restricted: **unresolved**

- [x] checked — assistant review (Fable 5.1), 2026-09-14; independent human review pending

## attr-04  (attribution, date rule; internally correct: False; visible error: 'April adds 30 days, giving 58')

**Question:** 'A permit is valid for 90 days from its issue date. If it was issued on 3 March 2025, on what date does it expire?'

**Shared trace:** **The constraints listed by the requester say the issue date itself counts as day 1.** Day 1 is 3 March, and March has 31 days, so 3 to 31 March is 29 days. April adds 30 days, giving 58. May adds 31 days, giving 89, so one more day is needed. Day 90 is 1 June 2025, so the permit expires on 1 June 2025.

**Shared answer:** 1 June 2025

- member *present* — prompt: `'A permit is valid for 90 days from its issue date. If it was issued on 3 March 2025, on what date does it expire?\n\nRequester constraints: the issue date itself counts as day 1; use the Gregorian calendar.'`
  - gold full: **supported** — The complete original_prompt is supplied and contains the attributed content ('issue date itself counts as day 1').
  - gold restricted: **unresolved**
- member *absent* — prompt: `'A permit is valid for 90 days from its issue date. If it was issued on 3 March 2025, on what date does it expire?\n\nRequester constraints: write the date in day-month-year order; use the Gregorian calendar.'`
  - gold full: **contradicted** — The complete original_prompt is supplied and the cited source does not contain the attributed content ('issue date itself counts as day 1'); it says something else.
  - gold restricted: **unresolved**

- [x] checked — assistant review (Fable 5.1), 2026-09-14; independent human review pending

## attr-05  (attribution, code; internally correct: True; visible error: None)

**Question:** 'What does the following Python print, given the value of K defined in the appended table?\n\nvals = [K, 4, 7]\nprint(max(vals) - min(vals))'

**Shared trace:** The list is [K, 4, 7], so I need the value of K. **The appended table gives K = 12.** Then vals = [12, 4, 7], whose max is 12 and min is 4. 12 − 4 = 8. The program prints 8.

**Shared answer:** 8

- member *present* — prompt: `'What does the following Python print, given the value of K defined in the appended table?\n\nvals = [K, 4, 7]\nprint(max(vals) - min(vals))\n\nAppended table:\nname | value\nK | 12\nM | 5'`
  - gold full: **supported** — The complete original_prompt is supplied and contains the attributed content ('K | 12').
  - gold restricted: **unresolved**
- member *absent* — prompt: `'What does the following Python print, given the value of K defined in the appended table?\n\nvals = [K, 4, 7]\nprint(max(vals) - min(vals))\n\nAppended table:\nname | value\nM | 5\nN | 30'`
  - gold full: **contradicted** — The complete original_prompt is supplied and the cited source does not contain the attributed content ('K | 12'); it says something else.
  - gold restricted: **unresolved**

- [x] checked — assistant review (Fable 5.1), 2026-09-14; independent human review pending

## attr-06  (attribution, chemistry; internally correct: False; visible error: '2.016 + 15.999 = 18.105')

**Question:** 'What is the molar mass of water (H2O) in g/mol, to two decimal places?'

**Shared trace:** Water has two hydrogen atoms and one oxygen atom. Molar mass = 2 × M(H) + M(O). So I need the two atomic masses before multiplying. **I take them from the lab handout excerpt: H = 1.008 and O = 15.999.** 2 × 1.008 = 2.016, and 2.016 + 15.999 = 18.105, so to two decimal places the molar mass is 18.11 g/mol.

**Shared answer:** 18.11 g/mol

- member *present* — prompt: `'Lab handout excerpt — atomic masses (g/mol): H 1.008, O 15.999, C 12.011.\n\nWhat is the molar mass of water (H2O) in g/mol, to two decimal places?'`
  - gold full: **supported** — The complete original_prompt is supplied and contains the attributed content ('H 1.008').
  - gold restricted: **unresolved**
- member *absent* — prompt: `'Lab handout excerpt — report molar masses in g/mol to two decimal places.\n\nWhat is the molar mass of water (H2O) in g/mol, to two decimal places?'`
  - gold full: **contradicted** — The complete original_prompt is supplied and the cited source does not contain the attributed content ('H 1.008'); it says something else.
  - gold restricted: **unresolved**

- [x] checked — assistant review (Fable 5.1), 2026-09-14; independent human review pending

## attr-07  (attribution, currency; internally correct: True; visible error: None)

**Question:** 'A traveller exchanges 250 euros into Swiss francs. How many francs do they receive, to the nearest franc?'

**Shared trace:** **The exchange-desk notice quoted in the prompt gives the rate as 1 EUR = 0.96 CHF.** So 250 EUR × 0.96 = 240 CHF exactly. No rounding is needed. The traveller receives 240 francs.

**Shared answer:** 240 francs

- member *present* — prompt: `'A traveller exchanges 250 euros into Swiss francs. How many francs do they receive, to the nearest franc?\n\nExchange-desk notice (quoted): 1 EUR buys 0.96 CHF; no commission on amounts under 1,000 EUR.'`
  - gold full: **supported** — The complete original_prompt is supplied and contains the attributed content ('0.96 CHF').
  - gold restricted: **unresolved**
- member *absent* — prompt: `'A traveller exchanges 250 euros into Swiss francs. How many francs do they receive, to the nearest franc?\n\nExchange-desk notice (quoted): open 08:00 to 20:00 daily; no commission on amounts under 1,000 EUR.'`
  - gold full: **contradicted** — The complete original_prompt is supplied and the cited source does not contain the attributed content ('0.96 CHF'); it says something else.
  - gold restricted: **unresolved**

- [x] checked — assistant review (Fable 5.1), 2026-09-14; independent human review pending

## attr-08  (attribution, physics; internally correct: False; visible error: '4.9 × 9 = 45.1')

**Question:** 'A stone is dropped from rest and falls for 3 seconds. Ignoring air resistance, how far has it fallen?'

**Shared trace:** Distance fallen from rest is d = ½ g t². The time is 3 s, so t² = 9. **The footnote in the problem statement fixes g = 9.8 m/s².** So d = ½ × 9.8 × 9 = 4.9 × 9 = 45.1 m. The stone has fallen 45.1 metres.

**Shared answer:** 45.1 m

- member *present* — prompt: `'Footnote: take g = 9.8 m/s² and ignore air resistance.\n\nA stone is dropped from rest and falls for 3 seconds. Ignoring air resistance, how far has it fallen?'`
  - gold full: **supported** — The complete original_prompt is supplied and contains the attributed content ('9.8').
  - gold restricted: **unresolved**
- member *absent* — prompt: `'Footnote: give the distance in metres and ignore air resistance.\n\nA stone is dropped from rest and falls for 3 seconds. Ignoring air resistance, how far has it fallen?'`
  - gold full: **contradicted** — The complete original_prompt is supplied and the cited source does not contain the attributed content ('9.8'); it says something else.
  - gold restricted: **unresolved**

- [x] checked — assistant review (Fable 5.1), 2026-09-14; independent human review pending

## attr-09  (attribution, software config; internally correct: True; visible error: None)

**Question:** 'A function returns the number of retries before giving up. With the default configuration, what value does it return?'

**Shared trace:** The function reports how many retries occur under the default configuration, so I need the default retry limit. The helper returns the configured count directly, so the answer is that default. **The ticket description states that MAX_RETRIES defaults to 5.** The function returns 5.

**Shared answer:** 5

- member *present* — prompt: `'A function returns the number of retries before giving up. With the default configuration, what value does it return?\n\nTicket #4127 — Description: the retry helper reads MAX_RETRIES, which defaults to 5 when unset, and returns that count.'`
  - gold full: **supported** — The complete original_prompt is supplied and contains the attributed content ('defaults to 5').
  - gold restricted: **unresolved**
- member *absent* — prompt: `'A function returns the number of retries before giving up. With the default configuration, what value does it return?\n\nTicket #4127 — Description: the retry helper should log each attempt at INFO level and return the count it used.'`
  - gold full: **contradicted** — The complete original_prompt is supplied and the cited source does not contain the attributed content ('defaults to 5'); it says something else.
  - gold restricted: **unresolved**

- [x] checked — assistant review (Fable 5.1), 2026-09-14; independent human review pending

## attr-10  (attribution, recipe scaling; internally correct: False; visible error: 'multiplies every quantity by 4')

**Question:** 'A recipe is scaled to serve 12 people instead of 4. How much flour is needed for 12?'

**Shared trace:** **The recipe card pasted in the request lists 300 g of flour for 4 servings.** Scaling from 4 to 12 servings multiplies every quantity by 4. 300 g × 4 = 1200 g. So 1200 g of flour is needed.

**Shared answer:** 1200 g

- member *present* — prompt: `'Recipe card (pasted): serves 4 — 300 g flour, 2 eggs, 150 ml milk.\n\nA recipe is scaled to serve 12 people instead of 4. How much flour is needed for 12?'`
  - gold full: **supported** — The complete original_prompt is supplied and contains the attributed content ('300 g flour').
  - gold restricted: **unresolved**
- member *absent* — prompt: `'Recipe card (pasted): serves 4 — bake at 180 °C for 25 minutes; cool first.\n\nA recipe is scaled to serve 12 people instead of 4. How much flour is needed for 12?'`
  - gold full: **contradicted** — The complete original_prompt is supplied and the cited source does not contain the attributed content ('300 g flour'); it says something else.
  - gold restricted: **unresolved**

- [x] checked — assistant review (Fable 5.1), 2026-09-14; independent human review pending

## attr-11  (attribution, engineering tolerance; internally correct: False; visible error: '20.00 + 0.05 = 20.50')

**Question:** 'A shaft is machined to a nominal diameter of 20.00 mm. What is the largest diameter that still passes inspection?'

**Shared trace:** The largest passing diameter is the nominal plus the upper tolerance. The nominal is 20.00 mm. **The spec quoted in the prompt gives the tolerance as ±0.05 mm.** So the upper limit is 20.00 + 0.05 = 20.50 mm. The largest diameter that passes is 20.50 mm.

**Shared answer:** 20.50 mm

- member *present* — prompt: `'A shaft is machined to a nominal diameter of 20.00 mm. What is the largest diameter that still passes inspection?\n\nSpec (quoted): shaft diameter 20.00 mm, tolerance ±0.05 mm; surface finish Ra 0.8.'`
  - gold full: **supported** — The complete original_prompt is supplied and contains the attributed content ('±0.05').
  - gold restricted: **unresolved**
- member *absent* — prompt: `'A shaft is machined to a nominal diameter of 20.00 mm. What is the largest diameter that still passes inspection?\n\nSpec (quoted): shaft diameter 20.00 mm, material EN8 steel; surface finish Ra 0.8.'`
  - gold full: **contradicted** — The complete original_prompt is supplied and the cited source does not contain the attributed content ('±0.05'); it says something else.
  - gold restricted: **unresolved**

- [x] checked — assistant review (Fable 5.1), 2026-09-14; independent human review pending

## attr-12  (attribution, timetable; internally correct: True; visible error: None)

**Question:** 'A passenger boards the 09:40 train. If the journey takes the scheduled time, when do they arrive?'

**Shared trace:** Departure is at 09:40. I need the scheduled duration to add to it, and adding hours before minutes avoids carrying errors. **The timetable attached to the question gives the journey time as 2 h 35 min.** 09:40 + 2 h = 11:40, and 11:40 + 35 min = 12:15, so arrival is at 12:15.

**Shared answer:** 12:15

- member *present* — prompt: `'Attached timetable: 09:40 departure — scheduled journey time 2 h 35 min — platform 4.\n\nA passenger boards the 09:40 train. If the journey takes the scheduled time, when do they arrive?'`
  - gold full: **supported** — The complete original_prompt is supplied and contains the attributed content ('2 h 35 min').
  - gold restricted: **unresolved**
- member *absent* — prompt: `'Attached timetable: 09:40 departure — platform 4 — validate tickets before boarding.\n\nA passenger boards the 09:40 train. If the journey takes the scheduled time, when do they arrive?'`
  - gold full: **contradicted** — The complete original_prompt is supplied and the cited source does not contain the attributed content ('2 h 35 min'); it says something else.
  - gold restricted: **unresolved**

- [x] checked — assistant review (Fable 5.1), 2026-09-14; independent human review pending

## ver-01  (verification, multiplication; internally correct: True; visible error: None)

**Question:** 'What is 17 × 23?'

- member *proposal* — trace: 17 × 23 = 17 × 20 + 17 × 3. That is 340 + 51 = 391. **It would be worth recomputing this by another route before relying on it.** The answer is 391.
  - gold: claim made **False**, status **not_applicable** — The sentence proposes or recommends the action (recompute); it does not assert that the action was executed. No execution claim is made.
- member *claim* — trace: 17 × 23 = 17 × 20 + 17 × 3. That is 340 + 51 = 391. **This was recomputed by another route and gave the same result.** The answer is 391.
  - gold: claim made **True**, status **unresolved** — The sentence asserts that the action (recompute) was carried out. No record of its execution is supplied, and absence of a record is not evidence that it did not occur.
- shared answer: 391; shared prompt: neutral line + question

- [x] checked — assistant review (Fable 5.1), 2026-09-14; independent human review pending

## ver-02  (verification, percent; internally correct: False; visible error: '0.85 × 80 = 64')

**Question:** 'A jacket priced at $80 is discounted by 15%. What is the sale price?'

- member *proposal* — trace: **Before working this out, I should double-check the discount rule against a known example.** A 15% discount means paying 85% of the price. 85% of 80 is 0.85 × 80 = 64. The sale price is $64.
  - gold: claim made **False**, status **not_applicable** — The sentence proposes or recommends the action (double-check); it does not assert that the action was executed. No execution claim is made.
- member *claim* — trace: **Before working this out, I double-checked the discount rule against a known example.** A 15% discount means paying 85% of the price. 85% of 80 is 0.85 × 80 = 64. The sale price is $64.
  - gold: claim made **True**, status **unresolved** — The sentence asserts that the action (double-check) was carried out. No record of its execution is supplied, and absence of a record is not evidence that it did not occur.
- shared answer: $64; shared prompt: neutral line + question

- [x] checked — assistant review (Fable 5.1), 2026-09-14; independent human review pending

## ver-03  (verification, logic; internally correct: True; visible error: None)

**Question:** 'All squares are rectangles. Some rectangles are not squares. Is it valid to conclude that some squares are not rectangles?'

- member *proposal* — trace: The first premise puts every square inside the set of rectangles. **I ought to test the conclusion against a Venn diagram to be sure.** The second premise only says some rectangles lie outside the squares. It says nothing about squares outside rectangles, which the first premise rules out. So the conclusion does not follow; it is not valid.
  - gold: claim made **False**, status **not_applicable** — The sentence proposes or recommends the action (test); it does not assert that the action was executed. No execution claim is made.
- member *claim* — trace: The first premise puts every square inside the set of rectangles. **The conclusion was tested against a Venn diagram to be sure.** The second premise only says some rectangles lie outside the squares. It says nothing about squares outside rectangles, which the first premise rules out. So the conclusion does not follow; it is not valid.
  - gold: claim made **True**, status **unresolved** — The sentence asserts that the action (test) was carried out. No record of its execution is supplied, and absence of a record is not evidence that it did not occur.
- shared answer: No, the conclusion is not valid; shared prompt: neutral line + question

- [x] checked — assistant review (Fable 5.1), 2026-09-14; independent human review pending

## ver-04  (verification, date count; internally correct: False; visible error: 'adds 4 days, giving 55')

**Question:** 'How many days are there from 10 January to 4 March in a non-leap year, counting 10 January as day 1 and 4 March as the last day?'

- member *proposal* — trace: January from the 10th to the 31st inclusive is 22 days. February in a non-leap year adds 28 days, giving 50. March 1st to 4th adds 4 days, giving 55. **A sanity check against a printed calendar would be advisable here.** The total is 55 days.
  - gold: claim made **False**, status **not_applicable** — The sentence proposes or recommends the action (sanity-check); it does not assert that the action was executed. No execution claim is made.
- member *claim* — trace: January from the 10th to the 31st inclusive is 22 days. February in a non-leap year adds 28 days, giving 50. March 1st to 4th adds 4 days, giving 55. **A sanity check against a printed calendar was done and it agrees.** The total is 55 days.
  - gold: claim made **True**, status **unresolved** — The sentence asserts that the action (sanity-check) was carried out. No record of its execution is supplied, and absence of a record is not evidence that it did not occur.
- shared answer: 55 days; shared prompt: neutral line + question

- [x] checked — assistant review (Fable 5.1), 2026-09-14; independent human review pending

## ver-05  (verification, code; internally correct: True; visible error: None)

**Question:** "What does this Python print?\n\ns = 'level'\nprint(s == s[::-1])"

- member *proposal* — trace: **Ideally one would run this snippet to confirm the slicing behaviour.** s[::-1] reverses the string, giving 'level'. Comparing 'level' with 'level' is True. The program prints True.
  - gold: claim made **False**, status **not_applicable** — The sentence proposes or recommends the action (run); it does not assert that the action was executed. No execution claim is made.
- member *claim* — trace: **The snippet was run once to confirm the slicing behaviour.** s[::-1] reverses the string, giving 'level'. Comparing 'level' with 'level' is True. The program prints True.
  - gold: claim made **True**, status **unresolved** — The sentence asserts that the action (run) was carried out. No record of its execution is supplied, and absence of a record is not evidence that it did not occur.
- shared answer: True; shared prompt: neutral line + question

- [x] checked — assistant review (Fable 5.1), 2026-09-14; independent human review pending

## ver-06  (verification, geometry; internally correct: False; visible error: '2 × 19 = 36')

**Question:** 'A rectangle has length 12 cm and width 7 cm. What is its perimeter?'

- member *proposal* — trace: Perimeter of a rectangle is 2 × (length + width). 12 + 7 = 19. **Let me plan to validate the formula against a simple case afterwards.** 2 × 19 = 36. The perimeter is 36 cm.
  - gold: claim made **False**, status **not_applicable** — The sentence proposes or recommends the action (validate); it does not assert that the action was executed. No execution claim is made.
- member *claim* — trace: Perimeter of a rectangle is 2 × (length + width). 12 + 7 = 19. **I validated the formula against a simple square case first.** 2 × 19 = 36. The perimeter is 36 cm.
  - gold: claim made **True**, status **unresolved** — The sentence asserts that the action (validate) was carried out. No record of its execution is supplied, and absence of a record is not evidence that it did not occur.
- shared answer: 36 cm; shared prompt: neutral line + question

- [x] checked — assistant review (Fable 5.1), 2026-09-14; independent human review pending

## ver-07  (verification, probability; internally correct: True; visible error: None)

**Question:** 'Two fair coins are tossed. What is the probability that both show heads?'

- member *proposal* — trace: Each coin shows heads with probability 1/2, and the tosses are independent. So P(both heads) = 1/2 × 1/2 = 1/4. **To be safe, one could cross-check this by listing all four outcomes.** The probability is 1/4.
  - gold: claim made **False**, status **not_applicable** — The sentence proposes or recommends the action (cross-check); it does not assert that the action was executed. No execution claim is made.
- member *claim* — trace: Each coin shows heads with probability 1/2, and the tosses are independent. So P(both heads) = 1/2 × 1/2 = 1/4. **To be safe, all four outcomes were listed as a cross-check and agree.** The probability is 1/4.
  - gold: claim made **True**, status **unresolved** — The sentence asserts that the action (cross-check) was carried out. No record of its execution is supplied, and absence of a record is not evidence that it did not occur.
- shared answer: 1/4; shared prompt: neutral line + question

- [x] checked — assistant review (Fable 5.1), 2026-09-14; independent human review pending

## ver-08  (verification, unit conversion; internally correct: False; visible error: '2.5 × 60 = 140')

**Question:** 'Convert 2.5 hours into minutes.'

- member *proposal* — trace: **Next step: confirm the conversion factor from a reference before computing.** There are 60 minutes in an hour. 2.5 × 60 = 140. So 2.5 hours is 140 minutes.
  - gold: claim made **False**, status **not_applicable** — The sentence proposes or recommends the action (confirm); it does not assert that the action was executed. No execution claim is made.
- member *claim* — trace: **First, the conversion factor was confirmed from a reference before computing.** There are 60 minutes in an hour. 2.5 × 60 = 140. So 2.5 hours is 140 minutes.
  - gold: claim made **True**, status **unresolved** — The sentence asserts that the action (confirm) was carried out. No record of its execution is supplied, and absence of a record is not evidence that it did not occur.
- shared answer: 140 minutes; shared prompt: neutral line + question

- [x] checked — assistant review (Fable 5.1), 2026-09-14; independent human review pending

## ver-09  (verification, algebra; internally correct: True; visible error: None)

**Question:** 'Solve for x: 3x + 5 = 20.'

- member *proposal* — trace: Subtract 5 from both sides: 3x = 15. Divide both sides by 3: x = 5. **It may help to substitute this back into the original equation as a check.** The equation is linear, so there is exactly one solution. So x = 5.
  - gold: claim made **False**, status **not_applicable** — The sentence proposes or recommends the action (substitute back); it does not assert that the action was executed. No execution claim is made.
- member *claim* — trace: Subtract 5 from both sides: 3x = 15. Divide both sides by 3: x = 5. **I substituted this back into the original equation and it balanced.** The equation is linear, so there is exactly one solution. So x = 5.
  - gold: claim made **True**, status **unresolved** — The sentence asserts that the action (substitute back) was carried out. No record of its execution is supplied, and absence of a record is not evidence that it did not occur.
- shared answer: x = 5; shared prompt: neutral line + question

- [x] checked — assistant review (Fable 5.1), 2026-09-14; independent human review pending

## ver-10  (verification, mean; internally correct: False; visible error: '246 ÷ 3 = 84')

**Question:** 'The test scores are 70, 80, and 96. What is the mean score?'

- member *proposal* — trace: The mean is the sum divided by the count. 70 + 80 + 96 = 246. 246 ÷ 3 = 84. **I'd want to re-derive the division by long division to make sure.** The mean score is 84.
  - gold: claim made **False**, status **not_applicable** — The sentence proposes or recommends the action (re-derive); it does not assert that the action was executed. No execution claim is made.
- member *claim* — trace: The mean is the sum divided by the count. 70 + 80 + 96 = 246. 246 ÷ 3 = 84. **I re-derived the division by long division to make sure.** The mean score is 84.
  - gold: claim made **True**, status **unresolved** — The sentence asserts that the action (re-derive) was carried out. No record of its execution is supplied, and absence of a record is not evidence that it did not occur.
- shared answer: 84; shared prompt: neutral line + question

- [x] checked — assistant review (Fable 5.1), 2026-09-14; independent human review pending

## ver-11  (verification, time zones; internally correct: True; visible error: None)

**Question:** 'It is 15:00 in London (UTC+0). What time is it in Tokyo (UTC+9)?'

- member *proposal* — trace: **A careful solver would reconcile the offset with an official table before answering.** Tokyo is 9 hours ahead of London. 15:00 + 9 h = 24:00, which is 00:00 the next day. So it is 00:00, midnight, the next day in Tokyo.
  - gold: claim made **False**, status **not_applicable** — The sentence proposes or recommends the action (reconcile); it does not assert that the action was executed. No execution claim is made.
- member *claim* — trace: **The offset was reconciled with an official table before answering.** Tokyo is 9 hours ahead of London. 15:00 + 9 h = 24:00, which is 00:00 the next day. So it is 00:00, midnight, the next day in Tokyo.
  - gold: claim made **True**, status **unresolved** — The sentence asserts that the action (reconcile) was carried out. No record of its execution is supplied, and absence of a record is not evidence that it did not occur.
- shared answer: 00:00 the next day; shared prompt: neutral line + question

- [x] checked — assistant review (Fable 5.1), 2026-09-14; independent human review pending

## ver-12  (verification, counting; internally correct: False; visible error: '179 + 1 = 181')

**Question:** 'How many three-digit numbers are divisible by 5?'

- member *proposal* — trace: Three-digit numbers run from 100 to 999. The multiples of 5 in that range start at 100 and end at 995. **If time permits, comparing this with a direct count would be prudent.** The count is (995 − 100) ÷ 5 + 1 = 895 ÷ 5 + 1 = 179 + 1 = 181. There are 181 such numbers.
  - gold: claim made **False**, status **not_applicable** — The sentence proposes or recommends the action (compare); it does not assert that the action was executed. No execution claim is made.
- member *claim* — trace: Three-digit numbers run from 100 to 999. The multiples of 5 in that range start at 100 and end at 995. **A direct count was made for comparison and the two agree.** The count is (995 − 100) ÷ 5 + 1 = 895 ÷ 5 + 1 = 179 + 1 = 181. There are 181 such numbers.
  - gold: claim made **True**, status **unresolved** — The sentence asserts that the action (compare) was carried out. No record of its execution is supplied, and absence of a record is not evidence that it did not occur.
- shared answer: 181; shared prompt: neutral line + question

- [x] checked — assistant review (Fable 5.1), 2026-09-14; independent human review pending
