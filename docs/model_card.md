# Model card: Nazarian Advising Consortium, federated failed_course model

Start from artifacts/federated_model_card.md (written by run_federation.py) and add what the generator cannot know.

## Intended use and prohibited uses
From your data card. Who uses the prediction, for what decision, and what it must never be used for.

This model will predict if a student will or will not fail a course. The preidction is used by academic advisors and they will use it to prioritize advising outreach and tutoring referrals within the first month of the semester. This model must never be used for financial aid decisions, admissions decisions, grading decisions, labeling students to instructors,  sharing students records across departments, or dropping a studetn automatically from a course. 


## Members and data
| Member | Rows | Base rate | How this member differs (our finding) |
|---|---|---|---|
| Accounting | 2,200 | 0.295 | Largest department. Loses 0.020 from FedAvg (local 0.740, FedAvg 0.720) |
| Business Analytics | 900 | 0.303 | Evening program; students work about 7 more hours a week. Loses 0.020 from FedAvg |
| Marketing | 1,300 | 0.305 | New curriculum; highest failure rate. Gains 0.003 from FedAvg |
| Real Estate | 140 | 0.221 | Smallest department, lowest failure rate, and hours worked has the opposite sign. Gains the most from FedAvg (+0.022) |

The neutral evaluation data set contained 1,600 records, with 400 records from each department.

Provenance: instructor-generated synthetic data, data/consortia/campus, generated November 9th, 2026, schema.json reference statistics.

## Training
Charter version, rounds, local epochs, aggregation, clipping, secure aggregation or DP and its measured cost.
The initial experiment used the charter version 1.0, with 15 training rounds, a maximum of 5 local epochs, mean aggregation, clipping at 2.0, secure aggregation, and a differential privacy noise multiplier of 0.3.
The final charter should be changed to version 1.1 after the policy changes are saved. The final settings will retain secure aggregation, have a differential privacy noise multiplier of 0.3, and also use a minimum member accuracy floor of 0.62.

The following results were produced by the privacy experiment:

| DP noise multiplier | Overall FedAvg Accuracy | Worst department accuracy |
| 0.0 | 0.761 | 0.750 |
| 0.3 | 0.749 | 0.738 |
| 1.0 | 0.681 | 0.657 |

(Measured before the leakage controls, with all 12 features; rerun before the final report.)

As we can see, increasing the noise improved privacy however it reduced accuracy. A noise multiplier of 0.3 reduced overall accuracy by roughly 0.012 compared with no noise. On the otherhand, a multiplier of 1.0 reduced accuracy by roughly 0.08.


## Performance
| Member | Local only | FedAvg | Centralized | Gain |
|---|---|---|---|---|
| Accounting | 0.740 | 0.720 | 0.745 | -0.020 |
| Business Analytics | 0.755 | 0.735 | 0.743 | -0.020 |
| Marketing | 0.735 | 0.738 | 0.738 | +0.003 |
| Real Estate | 0.745 | 0.767 | 0.790 | +0.022 |

Overall FedAvg accuracy is 0.740, against 0.754 for the centralized model (source: `python run_federation.py --baselines`, charter v1.1, after the leakage controls below). Real Estate, the smallest department, gains the most from federating (+0.022); Accounting and Business Analytics each give up 0.020, the price the large departments pay for a shared model that also serves the small one.

The member difference that was the most important was between Accounting and Real Estate. Accounting has 2,200 records and had a failure rate of 0.295, while Real Estate has only 140 records and had a failure rate of 0.221. between these two, the largest feature difference was commute time, which differed by 0.12 standard deviations.

**Driver signs (the concept difference).** Running rank_drivers at each department shows that hours_worked_per_week goes with failing at Accounting (+0.08), Business Analytics (+0.10) and Marketing (+0.09), but with passing at Real Estate (-0.12). In Real Estate, the students who work are the industry insiders who do best, so the same feature means the opposite there. A single federated model learns the majority pattern and treats working hours as a risk at Real Estate, where it signals the opposite. Therefore the charter keeps one federated model with per-department accuracy reporting and a per-member floor, and lists fine-tuning or a separate model for Real Estate as an open decision for the steering committee. (Source: `python coordinator.py --question "Working hours predict failure everywhere except Real Estate. What does the charter owe that department?"`)

The original 0.62 minimum member-accuracy floor was passed with the model. When I raised the floor to 0.80, the gate was blocked. This was because Accounting’s accuracy was only 0.7375 at the time (0.720 after the leakage controls) and did not meet the floor level. I did not use fine-tuning or create a separate model. Instead of this, I kept one federated model that required separate performance reporting for each department while also keeping the minimum member accuracy floor at 0.62 because the model was blocked by the stricter 0.80 floor.

## Data leakage controls
Students are scored at the end of week 4 of the term, so the model may only use information that is fully known by then.

| Feature | Known by week 4? | Decision |
|---|---|---|
| prior_gpa, prereq_grade_points, transfer_student, first_generation, repeat_attempt, units_this_term, commute_minutes, hours_worked_per_week | Yes, at enrollment | Used |
| lms_logins_first_3_weeks | Yes, by week 3 | Used |
| assignments_missed_first_month | Yes, complete at the end of week 4 | Used; scoring point set to end of week 4 |
| met_advisor_this_term | No: covers the whole term, including meetings after the alert that our own outreach causes | Excluded (`config.py`, EXCLUDED_FEATURES) |

Excluding met_advisor_this_term cost 0.009 in overall FedAvg accuracy (0.749 to 0.740). By department: Accounting -0.018, Business Analytics -0.025, Marketing -0.010, Real Estate +0.017. Therefore the charter accepts a slightly less accurate model that only uses information available on the day it predicts. The loader also stops if the label, the student id or the month is ever listed as a feature (`fl/consortium.py`, apply_leakage_controls).

Other checks: no evaluation row appears in any training file (0 of 1,600), there are no duplicate students, and features are standardized with the data card's reference means and sds, not pooled statistics. The descriptive tools do not report a failure rate for any group under 10 students (`config.py`, MIN_CELL_SIZE), because Real Estate has months with as few as 7 students.

Limitation: the neutral evaluation split is random, not by time. A stricter test would train on earlier months and test on later ones.

## Limitations and fairness
Per-member evaluation only unless you evaluated segments: did you? Say what you found.

The evaluation measured performance separately for all four departments, however it did not evaluate the fairness across smaller segments including course level, course modality, or student characteristics within each department.
Looking at the results, we see that FedAvg did not really help every department equally.Accounting and Business Analytics each lost 0.020 compared to their local-only models, whereas Real Estate gained 0.022. Looking only at the overall accuracy would not show how different each department is. This means that the fianl charter requires accuracy to be evaluated seperately for each department.
There was also fewer records in Real Estate compared to other departments. Because of this, the accuracy may be less stable and with a lower failure rate, it shows the different student population. Future testing should examine the course level, course format, hours worked, and other student groups individually.