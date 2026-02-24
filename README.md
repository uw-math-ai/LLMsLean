# Testing Large Language Models’ Autoformalization Capabilities in LEAN

A [UW Math AI Lab](https://github.com/uw-math-ai) project.

Within the past few years, the ability of Large Language Models (LLMs) to generate formal mathematical proofs has improved drastically. We will provide a comparison of various LLMs' effectiveness in producing a successful proof in the Lean 4 theorem prover on both Mini-F2F and Mini-CTX datasets. Specifically, we will compare three general purpose LLMs: Gemini 3-pro, Chat GPT 5.2, Claude 4.5 Opus, and three specialized LLMs: Kimina-72B, Goedel-Prover-32B, Deepseek-Prover-V2-7B. We plan to test each models effectiveness at Pass@4, and multi turn proof generation with $k=4$. Finally, we will analyze the cost, the number of tokens and the latency time to provide the optimal model given the available resources of the users. 

## Initial Tests

The following tracks the success rate of **Sonnet 4.5** as it is allowed multiple attempts to solve the problems from the MiniF2F dataset.

| Attempts | Number of Successes |
| --- | --- |
| 1 | 146 |
| 2 | 183 |
| 3 | 207 |
| 4 | 217 |
| 5 | 227 |


\
[![](https://mermaid.ink/img/pako:eNpFkU9vgzAMxb-KZWm3gAgJf8JhUrWpt56608oOGXhtNAhVGiRY1e--FNTNl-Q9_Z4ty1dshpawwtpOc3PSzkef5HVtIZQ3viOocT9YSx5knMFu7LyJ3kZnYdM0o9PNDIOFnbFmm25rXINTpCdzCcmN99Sf_aVGOHAGKQPBQDLIPlZwfoBPsB-bhqilNrAJRNEz8JXpjCU4JHGqFC8TkZYMklgU2f2Rqfz3pJR5kXLBF5FnPBdKyA9keHSmxcq7kRj25Hp9l3i996_Rn6inGqvwbbX7Xneo7S3kztq-D0P_iLphPJ6w-tLdJajx3GpPr0Yfne7_XEe2JfcyjNZjJVW-NMHqihNWnItYSKVUKQvJU84ZzlilKi6CWea5LLNMZcWN4c8yNYnLIktCiTIJawWAIbXGD263Hm253e0XnkCBUA?type=png)](https://mermaid.live/edit#pako:eNpFkU9vgzAMxb-KZWm3gAgJf8JhUrWpt56608oOGXhtNAhVGiRY1e--FNTNl-Q9_Z4ty1dshpawwtpOc3PSzkef5HVtIZQ3viOocT9YSx5knMFu7LyJ3kZnYdM0o9PNDIOFnbFmm25rXINTpCdzCcmN99Sf_aVGOHAGKQPBQDLIPlZwfoBPsB-bhqilNrAJRNEz8JXpjCU4JHGqFC8TkZYMklgU2f2Rqfz3pJR5kXLBF5FnPBdKyA9keHSmxcq7kRj25Hp9l3i996_Rn6inGqvwbbX7Xneo7S3kztq-D0P_iLphPJ6w-tLdJajx3GpPr0Yfne7_XEe2JfcyjNZjJVW-NMHqihNWnItYSKVUKQvJU84ZzlilKi6CWea5LLNMZcWN4c8yNYnLIktCiTIJawWAIbXGD263Hm253e0XnkCBUA)

