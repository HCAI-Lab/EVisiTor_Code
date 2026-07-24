# Typo-rate sweep: Full-Realistic model vs human data

Human reference: completion time 715.4 s (~95 s SD across steps), per-keystroke error (correction-episode) rate: formula 3.4%, word 6.3%.

| Condition | Runs | Completion time (s) | vs human | Error rate overall | Formula | Word | Backspaces/run |
|---|---|---|---|---|---|---|---|
| **Human (n=19..22 subj)** | — | 715.4 | — | — | 3.4% | 6.3% | — |
| 0% nominal | 25 | 690.0 ± 16.2 | -3.6% | 0.0% | 0.0% | 0.0% | 0.0 |
| 1% nominal | 25 | 699.3 ± 18.6 | -2.3% | 0.8% | 0.8% | 0.5% | 3.0 |
| 2% nominal | 25 | 703.4 ± 23.4 | -1.7% | 2.0% | 2.1% | 1.6% | 7.7 |
| 3% nominal | 25 | 714.3 ± 16.9 | -0.2% | 3.0% | 3.0% | 3.1% | 11.8 |
| 4% nominal | 25 | 716.7 ± 19.7 | +0.2% | 4.1% | 4.1% | 3.9% | 16.2 |
| 6% nominal | 25 | 717.5 ± 22.4 | +0.3% | 5.9% | 5.9% | 5.8% | 23.4 |
| 8% nominal | 25 | 733.9 ± 21.8 | +2.6% | 8.2% | 8.2% | 8.5% | 33.4 |
| 10% nominal | 25 | 750.1 ± 24.2 | +4.9% | 10.0% | 9.8% | 11.3% | 41.4 |
| 12% nominal | 25 | 756.6 ± 22.2 | +5.8% | 12.2% | 12.3% | 11.6% | 51.8 |
| human-calibrated | 150 | 712.3 ± 20.9 | -0.4% | 3.8% | 3.5% | 5.8% | 14.9 |

Notes: model error rates are *realized* rates (mismatched / content keystrokes) measured from keypresses.csv; the nominal rate is the per-keystroke injection probability. Human rates are observed correction episodes per content keystroke (uncorrected errors are not observable in the keystroke log), so both quantify corrected-error events per keystroke. The human-calibrated condition uses the rates measured from the participant data: formula 3.4%, word 6.3% per keystroke.
