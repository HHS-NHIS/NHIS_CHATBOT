Subject: Prototype NHIS Assistant / Estimate Chatbot Demo

Hi all,

I wanted to share a working prototype of an NHIS assistant that demonstrates how a conversational, widget-style interface could sit on top of existing NHIS data query resources. The prototype currently retrieves adult and child Summary Health Statistics estimates from controlled DHIS/NHIS data files, provides brief answers with confidence intervals where available, routes general NHIS questions to approved NHIS/participant resources, and includes optional GPT-style wording/follow-up support without allowing the model to generate estimates.

The tool is intended as a demo of how users could ask plain-language questions such as “What percent of adults had diabetes last year by SVI?” or “Where can I find the 2024 public use files?” and receive a concise, source-grounded response. It also includes a compact iframe version that could be embedded in a dev page for review.

This is not a production system yet. Recommended next steps would include source/governance review, formal UI/accessibility review, controlled live-data refresh, expanded documentation retrieval, and additional testing with real user questions before considering public release.

