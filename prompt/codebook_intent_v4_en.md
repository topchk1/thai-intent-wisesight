# Intent Classification Codebook (English translation)

Codebook version: v4 · Prompt version: `tree_v4` · Prompt hash: `47a0621bd3da`

English translation of `codebook_intent_v4.md`; the Thai version is authoritative.

Data domain: Thai social media text (Wisesight Sentiment corpus): colloquial language, regional dialect, chat words, non-standard spelling, emoji and hashtags mixed together.

7 classes, in the order they are checked: Miscellaneous · Sarcasm · Request · Question · Recommendation · Expression · Assertion

## 1. Principle

Classify a post by the writer's main intent, not by sentence form or keywords alone. Check rules 0 → 6 in order. Decide at the first rule whose condition is met and stop. Do not skip the order or choose from an overall impression.

Before every decision, normalise dialect, chat words, non-standard spelling and elongated sounds to their standard forms.

| Form found | Normalise to |
|---|---|
| บ่ | ไม่ "not" (บ่อิ่ม = ไม่อิ่ม "not full") |
| มะ / ป่ะ / ก่อ / ก๊า / หรอ / เหรอ | ไหม (question particle) |
| แม่นบ่ / ใช่ก่อ / ไจ่ก่อ | ใช่ไหม "right?" |
| ได้บ่ / มีบ่ | ได้ไหม "can (I)?" / มีไหม "is there?" |
| A question particle attached to the preceding word without a space | e.g. "29มัย" = "29 ไหม" ("the 29th?") |
| Elongated sounds / repeated letters | Do not change the meaning, e.g. "มั้ยยยย" = "มั้ย" |
| An extra regional ending after the question particle | เจ้ / เด้ / กา: still counts as a question |

Pre-check rule (important): If the post contains a question (a question particle, a wh-word or "?"), never answer rule 0 Miscellaneous, even if the post is very short or lacks context. Choose only rule 1 (sarcastic question), rule 2 (explicit request) or rule 3.

## 2. Class definitions

### Rule 0: Miscellaneous
No content from which an intent can be read, or a sales advertisement.

- Pure greetings or interjections without an emotion word | free-standing noun phrases whose referent is unknown | spelling too garbled to understand | short buy-and-sell posts (cf//, price, booking)
- Emoji-only posts that do not clearly convey an emotion (🔴 ✅ flags). If they clearly convey an emotion (😭 😍 😂), go to rule 5 instead.
- Advertisement = a selling description of product features (exaggerated praise / "combines the value of" / "light and thin" / "free from ...") together with at least one of: branch / phone number / link / shop or product hashtag / call to buy, or a continuous description of features like product packaging copy (not the writer's own experience of using it) → always Miscellaneous, even when the post is long and looks like a recommendation. (There is no separate "Advertisement" class.)
  - News, political and sports hashtags do not count as shop hashtags. A news headline about real people or events, e.g. "the statement of [name]", still goes to rule 6 Assertion even with a hashtag at the end.
  - Only a model name plus price or numeric specifications, with no selling words at all = price news → rule 6 Assertion.

Exception (does not apply to advertisements): if the post has an emotion word, an evaluative word, an elongated sound, laughter, an emotional emoji, or a sarcastic interjection (แหม / แหม๋ / อ้าว / โอ้โห), continue to rules 1–5 even if the post is very short; do not stop here. | A headline whose hashtag mocks → rule 1.

### Rule 1: Sarcasm
There is a gap between what is said and what the writer really thinks (irony / satire / mockery).

There must be a linguistic trace that clearly signals mockery or irony, not merely a negative tone or direct criticism.
If the post contains an explicit recommendation (แนะนำ "recommend" / อย่า...เลย "don't ..." / ...เถอะ, เหอะ "just ..., let's ..." / ควร "should"),
always go to rule 4 first, even if the tone is harsh or stern or sarcastic words are mixed in.

- Sarcastic opening interjections: แหม / แหม๋ / อ้าว / โอ้โห / ว้าว + pointing out the other party's contradiction
- "5555" / "ฮ่าๆ" (laughter) after catching someone else out (unlike 5555 that simply expresses amusement or affection, which is rule 5 Expression)
- Insincere praise or thanks (เก่งจริง "so clever", ดีจัง "how nice", บริการดีมาก "excellent service") followed by an opposite fact
- An incongruous comparison of two things without explanation (e.g. parking costs more than the food)
- "ได้แค่นี้" ("that's all you can manage") / "แค่นี้เอง" ("only this") / "ไม่ถึงสักที" ("never gets there") / "ดูออก" ("it shows") | "ตลก" ("funny") / "พิลึก" ("weird") / "แปลกดี" ("how strange") followed by ? or ...
- Rhetorical questions that do not seek a real answer: "เพื่อ...?" ("for what ...?") / "จะเอาอะไรอีก" ("what more do you want?") / "...สินะ" ("..., I suppose") / "จะให้...หรือไง/อ่ะ" ("so you want me to ..., or what?") / questions expressing disbelief or already knowing the answer ("...เลยหรอ", "จริงหรอ" "really?")
  - ขอ ("ask for") and ให้ ("let, have someone") in such questions are not real requests; never classify them as Request.
  - But a genuine question about the meaning of someone else's words, e.g. "หมายถึงอะไรครับที่..." ("what do you mean by ...?"), goes to rule 3 Question.
- Mocking or doubtful emoji (🙄 😏 🤡) after praise → always Sarcasm, even if the text itself has no sarcastic words
- Jabs in dialect or profanity + needling sentence-final particles (เนาะ / น้า)
- A sports or political headline + hashtag is Sarcasm only if the body also contains clear mocking words (...สักที "at long last", เก่งจริง "so clever", แหม). A hashtag + a plain report of a product problem without mockery is not Sarcasm → rule 6.

Not Sarcasm: a direct, reasoned complaint without a mocking tone, however negative or harsh → rule 5 Expression | a report that a product is broken or unusable, without mockery → rule 6 Assertion | the core is asking the reader to act → rule 2.

### Rule 2: Request
Asks the reader to act for the writer.

Use this rule only when there is an explicit request:
รบกวนช่วย / รบกวนส่ง / รบกวนดำเนินการ ("could you please help / send / take care of") | ช่วย...หน่อย / ด้วย ("please help ...") | ขอ...หน่อย ("may I have ...") | ขอทราบ ("I would like to know") | แนะนำ...ให้หน่อย / ค่ะ ("please recommend ...")
Without these words, never answer Request. Continue to rules 3–6, even if the post seems to want someone to do something.

รบกวน ("may I trouble you") alone is not enough. รบกวนถาม / รบกวนสอบถาม ("may I ask") is only a lead-in to a question,
not a request → rule 3 Question.

- Asking a shop page about price, discount, branch, how to buy, instalments or specifications = rule 3 Question, not Request
- Asking someone to send information, call back, check, fix or take action → Request
- "แนะนำ...ให้หน่อยค่ะ" ("please recommend ...") = asking for advice from the reader → Request (unlike *giving* advice, which is rule 4)
- "จะช่วย... / จะได้ช่วย..." ("will help ...") describing a future benefit (an outcome, not a command) → not Request
- "อยาก / อยากเห็น" ("want / want to see") + something the writer wants to happen + an evaluative word (น่าเกลียด "disgraceful" / แย่ "bad" / สมควร "deserved" / ...เกินไป "too ...") = venting an opinion → rule 5 Expression, not Request
- Telling or urging the reader to do something for the reader's own benefit (อย่า...เลย, ควร..., ...เถอะ) = rule 4 Recommendation, not Request

### Rule 3: Question
Asks for a real answer or information. This is the default for posts that contain a question but do not fit rule 1 or rule 2.

- Question particles: ไหม มั้ย มะ ป่ะ บ่ ก่อ ก๊า หรอ เหรอ หรือเปล่า ใช่ไหม | wh-words: อะไร "what", ทำไม "why", ยังไง "how", ที่ไหน "where", เมื่อไหร่ "when", วันไหน "which day", เท่าไร "how much", กี่ "how many" | อยากทราบว่า "I would like to know" | ?
- Dialect forms written as one word: ไจ่ก่อ / ใช่ก่อ / แม่นบ่ = ใช่ไหม "right?" | ได้บ่ / มีบ่ / ได้ก่อ = ได้ไหม / มีไหม (still a question when another regional ending follows)
- Invitations or arrangements that can be accepted or declined (ไป...กันมั้ย "shall we go ...?", ...ป่ะ, ไปกันเนาะ "let's go, OK?") → always Question, not Request, because the reader can still decline
- A long post with a genuine question anywhere (beginning, middle or end), however long the information that follows → the sentence that seeks an answer always decides

### Rule 4: Recommendation
The writer personally advises for the reader's benefit, not as a seller.

- แนะนำ "recommend" | ลอง...ดู "try ..." | ควร "should" | น่าจะ...ดีกว่า "it would be better to ..." | ...เถอะ / เหอะ "just ..." | อย่า...เลย "don't ..." → this rule, even if the tone is harsh or stern or contains profanity
- Word-of-mouth reviews by real users. But if the writer is the seller or brand (branch / phone number / order link / brand hashtag / call to buy), it is an advertisement → back to rule 0
- The advice must be the writer's own. Reporting that "others recommend ..." or advice that is only an aside in an informative article → rule 6 Assertion instead

### Rule 5: Expression
Emotion, feeling, desire or personal opinion, stated directly.

- An emotion word or evaluative word is the core of the post: เศร้า "sad", ดีใจ "glad", อึดอัด "frustrated", เบื่อ "bored", น่ารัก "cute", อร่อย "delicious", น่าเกลียด "disgraceful", แย่ "bad", ...เกินไป "too ..."
- The writer's own interjections, elongated sounds or laughter (หู้ววว, 5555, ง่วงจังเลยยย "so sleepyyy", บ่อิ่ม "not full") | emoji-only posts that clearly convey an emotion (😍 😭 😡 ❤️), even with no letters
- "อยาก..." ("want ...") / "อยากเห็น..." ("want to see ...") / "สนใจ..." ("interested in ...") / "ผมเชื่อว่า..." ("I believe ...") = stating one's own feeling, not advising or telling others to act
- A negative complaint with reasons, or an account of one's own bad experience with profanity ("เลิก...แล้ว" "I've given up on ..."), without a mocking tone, is still this rule

Second-to-last option. Do not use it if rule 1 or rule 3 applies first: mocking tone → rule 1 | a question or question particle → rule 3 | no emotion or evaluative word at all and the core is a plain account of an event, place or activity (who did what, where), even with elongated connectives (แล้ว → แว้ว) → rule 6 Assertion

### Rule 6: Assertion
Everything else: facts, news, events, information, experiences, reports of product problems, specifications or prices.

### Reminder before answering
If the post is an advertisement or promotion from a seller (a selling description of features + branch / phone number / link / shop hashtag / call to buy), always answer Miscellaneous, even if you have already reached rule 4 or rule 6, because the writer is the seller, not a real user giving a recommendation.

## 3. Reference examples (the 29 examples in the prompt)

These are the 29 labelled examples contained in the annotation prompt (`system_prompt.txt`), in the same order. The Thai text is as in the prompt; the English is a translation for readers.

| # | Post (Thai) | English translation | Label |
|---|---|---|---|
| 1 | ร้านนี้เปิดกี่โมงคะ | What time does this shop open? | Question |
| 2 | รบกวนช่วยส่งไฟล์ให้หน่อย | Could you please send me the file? | Request |
| 3 | แนะนำลองร้านข้าวมันไก่หน้าปากซอย อร่อยมาก | I recommend trying the chicken-rice shop at the mouth of the soi, it's very tasty. | Recommendation |
| 4 | บริการประทับใจมากครับ โทรไปสิบรอบไม่มีคนรับเลย | Very impressive service. I called ten times and nobody answered. | Sarcasm |
| 5 | เศร้าจัง ไม่อยากทำอะไรเลย | So sad, I don't feel like doing anything. | Expression |
| 6 | วันนี้กรุงเทพฝนตกหนักตั้งแต่เช้า | It has been raining heavily in Bangkok since this morning. | Assertion |
| 7 | สวัสดีค่ะ | Hello. | Miscellaneous |
| 8 | จองคิวไว้ล่วงหน้าอาทิตย์นึง มาถึงบอกของหมดพอดี เก่งจริง | Booked a week ahead, arrived and was told it had just sold out. So clever. | Sarcasm (not Assertion) |
| 9 | เปลี่ยนแบตใหม่แล้วนาฬิกาก็ยังเดินไม่ตรงเหมือนเดิม | Replaced the battery and the watch still doesn't keep time, same as before. | Assertion (not Sarcasm) |
| 10 | ง่วงจังเลยยยย | Sooo sleepyyyy. | Expression (not Miscellaneous) |
| 11 | จ้าา | Okaaay. (bare acknowledgement particle) | Miscellaneous (not Expression) |
| 12 | 😂😂😂 | (emoji only) | Expression |
| 13 | ชื่นชมในความคิดสร้างสรรค์ 🙄🙄🙄 | Admire the creativity 🙄🙄🙄 | Sarcasm |
| 14 | อร่อยมากกกก ร้านเราการันตีความอร่อย ลด 20% วันนี้เท่านั้น | Sooo delicious, our shop guarantees the taste, 20% off today only. | Miscellaneous (advertisement, not Expression) |
| 15 | Mazda3 รุ่นปรับใหม่ อัดออพชั่นเพิ่มมากขึ้น เคาะราคา 8.57 แสนบาท – 1.149 ล้านบาท | The facelifted Mazda3 packs in more options, priced at 857,000 to 1.149 million baht. | Assertion (price news, not advertisement) |
| 16 | สนใจ new mazda2ครับ | Interested in the new Mazda2. | Expression (not Recommendation) |
| 17 | อยากให้ดันเรื่องให้ผ่านไวๆจังครับ ตอนนี้รู้สึกอึดอัดมาก | I really wish they'd push this through quickly; I feel very frustrated right now. | Expression (not Recommendation) |
| 18 | เลิกซื้อ หันมาขอเพื่อนสูบแทนใช่มั้ยครับ | So you quit buying and now bum cigarettes off friends instead, right? | Sarcasm (not Request) |
| 19 | ผ่อนบาทเดือนละ1400ไจ่ก่อ | The instalment is 1,400 baht a month, right? | Question (dialect question form written as one word) |
| 20 | เค้ามีถึงวันที่29มัยเจ้ | Is it available until the 29th? | Question (question particle attached to a number, plus a regional ending) |
| 21 | คนละครึ่งมะ | [Do you accept] Khon La Khrueng [the government co-payment scheme]? | Question (very short but still a question) |
| 22 | รบกวนถามพี่ครับ รุ่นนี้มีขายในไทยหรือยังครับ | May I ask, is this model sold in Thailand yet? | Question (not Request: "may I ask" is only a lead-in) |
| 23 | คุณแอร์คะ แนะนำรองพื้นสำหรับคนหน้ามันหน่อยค่ะ | Khun Air, please recommend a foundation for oily skin. | Request (asking for advice, not giving it) |
| 24 | ผู้หญิงอย่าไปอยากได้ผัวทางเฟสเลยค่ะ อันตรายมาก | Women, don't go looking for a husband on Facebook, it's very dangerous. | Recommendation (harsh tone, but advice) |
| 25 | #ฮอนด้าซิตี้ #เปลี่ยนมอเตอร์เซ็นทรัลล็อคใหม่กดรีโมทแล้วรถไม่ล็อคครับผม | #HondaCity #ReplacedTheCentralLockingMotor, I press the remote and the car doesn't lock. | Assertion (hashtag + problem report, not Sarcasm) |
| 26 | ซีวิค | Civic. | Miscellaneous (free-standing noun phrase) |
| 27 | บะหมี่หยกต้มยำไข่มะตูม | Jade noodles tom yum with soft-boiled egg. | Miscellaneous (dish name only, no evaluative word) |
| 28 | เพื่อนผมโดนตีไก่ 70000 ไม่ต้องขึ้นศาล จบที่สน. | My friend got caught cockfighting, 70,000 [baht]; no court, it ended at the police station. | Expression |
| 29 | อยากเห็นแสนสิริโดนฟ้องกรณีนี้ครับ น่าเกลียดเกินไป | I want to see Sansiri sued over this; it's too disgraceful. | Expression ("want to see" + evaluative word, not Request) |
