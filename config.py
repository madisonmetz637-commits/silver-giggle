# The one line every team changes: the folder under data/consortia/ you drew on Nov 16.
CONSORTIUM = "campus"

# The member whose record-level questions this agent may answer (predictions and actions on individual records).
# Aggregate questions (counts, rates, comparisons) are allowed for every member; record-level ones only here.
HOME_MEMBER = "Accounting"

# DATA LEAKAGE CONTROLS
# Students are scored at the END OF WEEK 4 of the term. A feature may be used by the model only if its value
# is fully known at that moment. Features listed here stay in the data (the descriptive tools can still show them)
# but are removed before training and scoring, with the reason recorded.
EXCLUDED_FEATURES = {
    "met_advisor_this_term": "covers the whole term, so it includes advisor meetings after week 4, "
                             "including meetings our own outreach causes; not known at scoring time",
}

# Small-cell suppression: the descriptive tools do not report an outcome rate for any group smaller than this,
# so a rate for a tiny group (for example one month at Real Estate) cannot point to individual students.
MIN_CELL_SIZE = 10
