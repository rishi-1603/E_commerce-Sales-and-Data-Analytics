// Customers_Transform.m
let
    Source = Csv.Document(File.Contents("data/raw_customers.csv"), [Delimiter=",", Columns=6, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{
        {"customer_id", Int64.Type},
        {"signup_date", type date},
        {"customer_segment", type text},
        {"region", type text},
        {"city", type text}
    }),
    #"Removed Duplicates" = Table.Distinct(#"Changed Type", {"customer_id"})
in
    #"Removed Duplicates"
