// Orders_Transform.m
let
    Source = Csv.Document(File.Contents("data/raw_orders.csv"), [Delimiter=",", Columns=10, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{
        {"order_id", Int64.Type},
        {"customer_id", Int64.Type},
        {"order_date", type date},
        {"order_status", type text},
        {"product_id", Int64.Type},
        {"quantity", Int64.Type},
        {"unit_price", type number},
        {"discount_percent", type number},
        {"order_item_total", type number}
    }),
    #"Filtered Invalid Status" = Table.SelectRows(#"Changed Type", each [order_status] <> null and [order_status] <> ""),
    #"Cleaned Dates" = Table.SelectRows(#"Filtered Invalid Status", each [order_date] >= #date(2023, 1, 1))
in
    #"Cleaned Dates"
