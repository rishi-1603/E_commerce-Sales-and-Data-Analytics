"""Strip auto date/time variation blocks that reference LocalDateTable objects.

Power BI generates those LocalDateTable_* tables itself when auto date/time is
on. Writing the variation into TMDL without the generated table makes the PBIP
fail to deserialize ("DefaultHierarchy ... refers to an object which cannot be
found"). Removing the blocks leaves a plain date column, which is what the
model's own Dim_Calendar already provides.
"""
import re

FILES = [
    r"C:\Users\user\portfolio-roadmaps\repos\ecom\powerbi\pbix\EcomAnalytics.SemanticModel\definition\tables\Dim_Calendar.tmdl",
    r"C:\Users\user\portfolio-roadmaps\repos\ecom\powerbi\pbix\EcomAnalytics.SemanticModel\definition\tables\Dim_Customers.tmdl",
]

PATTERN = re.compile(
    r"\n\t\tvariation Variation\n"
    r"\t\t\tisDefault\n"
    r"\t\t\trelationship: [0-9a-f-]+\n"
    r"\t\t\tdefaultHierarchy: LocalDateTable_[0-9a-f-]+\.'Date Hierarchy'\n"
)

for path in FILES:
    with open(path, encoding="utf-8") as f:
        text = f.read()
    new, n = PATTERN.subn("", text)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(new)
    print(f"{path.split(chr(92))[-1]}: removed {n} variation block(s)")
    print("  remaining LocalDateTable refs:", new.count("LocalDateTable"))
