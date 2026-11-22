# Model card: <your consortium>, federated <outcome> model

Start from artifacts/federated_model_card.md (written by run_federation.py) and add what the generator cannot know.

## Intended use and prohibited uses
From your data card. Who uses the prediction, for what decision, and what it must never be used for.

This model will predict if a student will or will not fail a course. The preidction is used by academic advisors and they will use it to prioritize advising outreach and tutoring referrals within the first month of the semester. This model must never be used for financial aid decisions, admissions decisions, grading decisions, labeling students to instructors,  sharing students records across departments, or dropping a studetn automatically from a course. 


## Members and data
| Member | Rows | Base rate | How this member differs (your finding) |
| Accounting | 2,200 | 0.295 | Is the largest department. The FedAvg accuracy decreased compared with its local only model |
| Business Analytics | 900 | 0.303 | Is an evening program The FedAvg accuracy increased by 0.012 |
| Marketing | 1,300 | 0.305 | There is a new curriculum and it also has the highest failure rate. The FedAvg accuracy increased by 0.005 |
| Real Estate | 140 | 0.221 | Is the smallest department and has the lowest failure rate. The FedAvg accuracy increased by 0.005 |

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

As we can see, increasing the noise improved privacy however it reduced accuracy. A noise multiplier of 0.3 reduced overall accuracy by roughly 0.012 compared with no noise. On the otherhand, a multiplier of 1.0 reduced accuracy by roughly 0.08.


## Performance
| Member | Local only | FedAvg | Centralized | Gain |
| Accounting | 0.748 | 0.738 | 0.750 | -0.010 |
| Business Analytics | 0.748 | 0.760 | 0.752 | +0.012 |
| Marketing | 0.743 | 0.748 | 0.752 | +0.005 |
| Real Estate | 0.745 | 0.750 | 0.782 | +0.005 |

The overall FedAvg accuracy was 0.749, rather than 0.759 for the centralized model.

The member difference that was the most important was between Accounting and Real Estate. Accounting has 2,200 records and had a failure rate of 0.295, while Real Estate has only 140 records and had a failure rate of 0.221. between these two, the largest feature difference was commute time, which differed by 0.12 standard deviations.

The original 0.62 minimum member-accuracy floor was passed with the model. When I raised the floor to 0.80, the gate was blocked. This was because Accounting’s accuracy was only 0.7375 and did not meet the floor level. I did not use fine-tuning or create a separate model. Instead of this, I kept one federated model that required separate performance reporting for each department while also keeping the minimum member accuracy floor at 0.62 because the model was blocked by the stricter 0.80 floor.

## Limitations and fairness
Per-member evaluation only unless you evaluated segments: did you? Say what you found.

The evaluation measured performance separately for all four departments, however it did not evaluate the fairness across smaller segments including course level, course modality, or student characteristics within each department.
Looking at the results, we see that FedAvg did not really help every department equally.Accounting lost 0.010 compared to the local-only model, whereas Business Analytics gained 0.012. Looking only at the overall accuracy would not show how different each department is. This means that the fianl charter requires accuracy to be evaluated seperately for each department.
There was also fewer records in Real Estate compared to other departments. Because of this, the accuracy may be less stable and with a lower failure rate, it shows the different student population. Future testing should examine the course level, course format, hours worked, and other student groups individually.