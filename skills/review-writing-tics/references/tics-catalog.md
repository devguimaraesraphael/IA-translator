# Reference: Catalog of Language Tics and Repeated Structure

> Entries below are **English examples**. When reviewing a text in another language, swap each
> word, verb and formula for the equivalent in the language of the text under review, keeping the
> same categories, thresholds and intentionality test. Categories that depend on a language's
> grammar (e.g. B.8, hypothetical comparisons) may have no direct analogue: keep the category,
> note it as language-specific, and adapt it.

> Consumed by `review-writing-tics`. Also relevant to `check-consistency` (narrative-style
> dimension, when repetition crosses chapters) and `create-style-guide` (to tell a voice motif
> from an accidental tic).

A language tic is a word, gesture or structure that recurs **out of writing reflex**, not by
deliberate choice. The symptom is not the word itself but the functionless repetition: the same
device solving the same problem (tension, contrast, eye contact) so many times that the reader
stops noticing each instance and starts noticing the pattern.

## A) How to count

1. **Group by lemma, not by exact form.** "Gripped", "grips", "grip", "gripping" count together.
   Counting only the exact form (`grep -c "gripped"`) understates the problem.
2. **Separate narration from dialogue.** The repetition rules in section C apply only to the
   narrator's voice. Character speech has its own logic: it may repeat through verbal habit,
   rhetorical insistence or deliberate dramatic tension.
3. **Normalize by text length**, but treat short chapters (< 3,000 words) with caution: the
   thresholds below assume dense, dialogue-heavy prose; a very short chapter can trip a threshold
   with few real occurrences and still not be a problem.
4. **Check proximity, not just total frequency.** Two occurrences of the same verb five paragraphs
   apart weigh less than two in the same paragraph or in consecutive lines of speech.

## B) Taxonomy, thresholds and examples

Thresholds are alert heuristics (not hard rules): they decide what is worth investigating with
the section C test, not what to cut automatically.

### 1. Contrast connectives (but, yet, however, still)
**Threshold:** more than ~6 occurrences of "but" (or equivalents) per 1,000 words of narration, or
more than 1 every 2-3 consecutive paragraphs.
**Symptom:** almost every emotional, physical or dialogue turn pivots on the same connective, and
the reader predicts the turn before the sentence ends.
**Example:** a 2,570-word chapter with 16 occurrences of "but", nearly one per 160 words,
covering gestures, lines and physical reactions indistinguishably.

### 2. Gesture verbs (grip, clutch, grab, touch, pull)
**Threshold:** the same gesture verb, with the same emotional meaning (tension, control,
affection), more than 2-3 times in the same chapter.
**Symptom:** the physical gesture is genuine and symbolic the first or second time; by the fifth
it is a mold: every handshake, wrist or object takes the same verb.
**Example:** "gripped" covering a bow, a wrist, a pendant and a hand saying goodbye: four
physically distinct gestures, all verbalized with the same word.
**Other typical English gesture tics:** sighed, nodded, shrugged, swallowed hard, let out a breath
he didn't know he was holding, ran a hand through his hair.

### 3. Eye-contact or default speech verbs (stare, gaze, say)
**Threshold:** the same eye-contact verb more than 2-3 times per chapter covering exchanges of
looks with different meanings (challenge, intimacy, accusation).
**Symptom:** every time two characters look at each other with dramatic weight, the narrator
reaches for the same verb, losing the chance to differentiate the **kind** of look through the
chosen verb.
**Typical English formulas:** "his eyes met hers", "she locked eyes with him", "he held her gaze".

### 4. Repeated gesture nouns (raised chin, clenched fist, set jaw)
**Threshold:** the same body detail, with the same emotional meaning (defiance, authority,
restraint), more than 2 times per chapter.
**Symptom:** the character's body has a "default gesture" for every assertion or confrontation
scene, instead of the gesture varying with the scene's intensity or context.

### 5. Redundant manner adverbs (slowly, quickly, quietly)
**Threshold:** any adverb that repeats information already in the verb ("dragged... slowly",
"ran... quickly") is a cut candidate regardless of frequency. As reinforcement: more than 2
occurrences of the same adverb a few paragraphs apart, even when describing different characters
or events.
**Symptom:** the narrator uses the same adverb to texture scenes that should already convey pace
through verb choice or syntax (short sentence = fast; long, flowing sentence = slow).
**Typical English forms:** "suddenly", "just", "simply", "slowly", "quietly", and the stock
"then" used to chain actions ("then he stood, then he turned").

### 6. Closing formulas for speech or paragraphs ("he said at last"; "and smiled"; "without another word")
**Threshold:** any **identical** closing formula used 2+ times in the same chapter, especially
closing distinct dramatic moments.
**Symptom:** the same sentence tail ends different scenes or lines, draining the second use of
weight, because the reader recognizes the pattern instead of feeling the moment.

### 7. Fixed sentence or paragraph openings (Name + verb, always in the same order)
**Threshold:** 3+ consecutive paragraphs opening with the same syntactic structure (e.g. always
"Name did X"), or the same name opening 3+ paragraphs on one page.
**Symptom:** the text creates a visual and syntactic metronome that the reader feels before being
able to name it. For broader rhythm analysis, see the project's chapter-review skill, if one
exists (this category is the specific case of repeated opening syntax).

### 8. Hypothetical comparative structures ("as if", "as though", "like")
**Threshold:** more than 4-5 occurrences of "as if" (or equivalent) per chapter, or 2+
occurrences in the same scene or paragraph.
**Symptom:** the narrator uses the hypothetical comparison as a stock tool for any ambiguous
gesture or reaction, even when the real cause of the emotion is already known; the hypothesis
becomes a distancing crutch instead of a genuine device for ambiguity.
**Language note:** the construction is common in English ("as if", "as though", "like he was...")
and in many other languages; adapt the trigger phrases to the language under review.
**Specific test (in addition to section C):** ask whether the narrator **already knows** the cause
of the described reaction. If so (one character's fatigue, another's fear), "as if" is narrative
cowardice: it states by comparison instead of showing directly, and becomes a tic. If not, because
the POV is genuinely speculating about an external cause it cannot confirm (e.g. two characters
interpreting a noise as a threat), the hypothesis is functional and should stay.
**Example:** a chapter had 7 occurrences of "as if" covering gestures whose cause the narrator
already knew (a hand hiding weakness, fatigue, fear, legs giving way), reduced to 1 occurrence
(the only one with an active, genuine hypothesis from the characters).
**Rewrite recipe (5 structures, each with a distinct effect, not interchangeable):**
1. *Direct metaphorical fusion*: the action IS the image, not "like" it.
   > "his legs buckled as if giving out" → "his legs gave out"
2. *Participle or gerund of intent*: replace the hypothesis with a reduced clause stating the
   gesture's purpose.
   > "a steady gesture, as if trying to hide any sign of weakness" → "a steady gesture, hiding
   > any sign of weakness"
3. *Paratactic juxtaposition*: cut the comparison and let the reader build the bridge between two
   short images.
   > "his chest throbbing as if he had screamed without opening his mouth" → "his chest throbbed,
   > a scream caught behind his teeth"
4. *Organic metaphor anchored in the world*: compare to something from the story's universe
   instead of a generic image.
   > "bubbling slowly as if alive" → "it pulsed slowly, at the rhythm of a sleeping engine"
5. *Comparison by effect, not cause*: narrate the observable physical consequence instead of
   speculating on the inner cause.
   > "leaned on the table as if his legs were failing" → "leaned on the table before his legs
   > could give out"

## C) Intentionality test: motif vs. tic

Before reporting any occurrence as a tic, ask:

1. **Does it evolve?** Does the element change in meaning, intensity or context over the text
   (e.g. a gesture that appears restrained at the start and violent at the climax)? If so, it is a
   motif in development, not a tic: static repetition is the problem, not repetition itself.
2. **Is it anchored by a world rule?** Is there an established rule in the project's bible that
   demands the same gesture or word (e.g. a magic item that reacts to a specific gesture)? If so,
   it is a world rule, not a tic: confirm against the bible before suggesting a cut.
3. **Is it a deliberate rhetorical echo?** Is the repetition a conscious refrain (the same line
   repeated by two characters in mirrored moments, a textual callback to an earlier scene)?
   Deliberate echoes usually appear in **pairs or triplets spaced with purpose**, not scattered
   without pattern across the text; if the author clearly structured the echo (same line,
   emotionally equivalent moments), preserve it.
4. **Is it a character's verbal habit?** In speech (not narration), repetition can be a voice
   trait: a character who always repeats an expression is a characterization choice, not a
   narrator tic. Check whether the pattern is consistent for that character in other chapters.
5. **Is it the only correct word?** Some words have no functional synonym without distorting the
   meaning (proper nouns, technical terms of the fictional world, anchor vocabulary of the
   scene's semantic field). Do not force variation in those cases.

If the answer to any of questions 1-4 is "yes" with concrete justification (not assumption),
classify as **intentional motif** and do not suggest a cut: only record the observation. If none
applies, it is an **accidental tic**, a rewrite candidate.

**Borderline** zone: when the answer is "maybe" (e.g. it looks like an echo but there is no
confirmation of authorial intent), report it as borderline and leave the final decision to the
author instead of deciding for them.

## D) Rewrite recipes by category

**Recipe 1: Contrast connective → cut with punctuation.**
Instead of swapping "but" for "yet"/"however" repeatedly (it only moves the tic), split the
sentence and leave the contrast implicit in the juxtaposition.
> "He felt cold, shivering slightly, but did not move or cover himself." →
> "He felt cold, shivering slightly. He did not move. He did not cover himself."

**Recipe 2: Contrast connective → "not X, but Y" restructured.**
When the contrast is a negation followed by an affirmation, rebuild it without the connective.
> "The ground turned black, not burned but emptied." →
> "The ground turned black: emptied, not burned."

**Recipe 3: Gesture verb → vary by the physical type of gesture, not by generic synonym.**
Each instance of the "mold verb" should become a verb describing the real mechanics of that
specific gesture, not an interchangeable synonym.
> "gripped the bow" → "his fingers locked on the bow" (muscular tension, not generic grip)
> "gripped her wrist" → "pinned her wrist" (restraint, not pressure)
> "he held her by the hem of her skirt" → "he tugged at the hem of her skirt" (childlike gesture,
> not restraint)

**Recipe 4: Eye-contact verb → replace with the result of the look, not the act of looking.**
Instead of swapping "stared" for another looking verb, describe what the look conveys or its
physical effect.
> "she stared at him" → "she did not look away" (persistence, not just contact)
> "staring at Marcus" → "her eyes fixed on Marcus" (shift the verb into noun plus adjective,
> varying the syntactic structure, not only the vocabulary)

**Recipe 5: Gesture noun → change the body gesture, not the word describing it.**
If "raised chin" was already used for defiance, the next defiance scene should use a different
body posture (shoulders, chest, hands) so the bodily cliché does not repeat.
> "with her chin raised" → "chest out, not giving an inch"
> "lifted his chin" → "squared his shoulders"

**Recipe 6: Redundant adverb → cut it or move the information into the verb or syntax.**
> "walked... slowly, unhurried" (redundant) → "walked... unhurried" (simple cut)
> "a slow step" → "a heavy step" (shifts the sensory axis from speed to weight, avoiding repeating
> the same idea of slowness already used for another character in the same scene)

**Recipe 7: Repeated closing formula → vary the kind of information in the closing.**
Instead of repeating the same tail, the second closing can bring a new layer (time, hesitation,
gesture) instead of merely marking the end of the line.
> "'Take the prisoner away,' he said at last." (1st use, kept)
> "'I'll set this aside,' he said at last." (2nd use, repeated) →
> "'I'll set this aside,' he said, after a long silence."

**Recipe 8: Fixed paragraph opening → vary the element that opens the sentence.**
Alternate between opening with the subject, an adverb or circumstance, a physical action, or
direct dialogue, instead of always "Name + verb".
> "She walked to..." / "She looked at..." / "She picked up..." (3 identical openings in a row) →
> vary at least one to open on the action or the setting: "Heavy steps crossed the corridor
> before she reached the door."

## E) Common mistakes when applying this skill

- **Witch hunt:** reporting every repetition without applying the section C test first. Not every
  repeated word is a tic: voice motifs and world rules are the opposite of the problem.
- **1:1 substitution that creates a new tic:** replacing every occurrence of one word with the
  same alternative recreates the tic under another name. Each occurrence should get a distinct
  solution whenever possible.
- **Ignoring dialogue vs. narration:** applying the narration threshold to a character's speech
  can erase a genuine voice trait (verbal habit).
- **Fixing too early:** running this skill on a still-unstable draft produces duplicate work; wait
  for the prose to settle (after the voice and rhythm pass).
- **Focusing only on isolated words and ignoring structure:** repeated connectives, paragraph
  openings and closing formulas usually hurt rhythm more than a repeated content word; do not
  leave categories 1, 6 and 7 out for being "less obvious" than a repeated noun.

## F) Reference metrics (per ~2,500-3,000 words of dense, dialogue-heavy narration)

- Dominant contrast connective (but/yet/however): ≤ 8-10 total occurrences, with no cluster of 3+
  in the same block of paragraphs
- Same gesture verb with the same emotional meaning: ≤ 2-3 occurrences
- Same eye-contact or default speech verb: ≤ 2-3 occurrences
- Same gesture noun with the same emotional meaning: ≤ 2 occurrences
- Manner adverb redundant with the verb: ideally 0, almost always cuttable
- Identical closing formula for speech or paragraphs: 0 literal repetitions, always vary
- Consecutive paragraphs with identical syntactic opening: ≤ 2 in a row
- "As if" (or equivalent) with a cause the narrator already knows: ≤ 3-4 total occurrences, never
  2+ in the same scene or paragraph

These metrics are a starting point, not law: a fast action chapter can justify more deliberate
rhythmic repetition; the section C judgment always prevails over the number.
