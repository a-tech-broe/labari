output "api_endpoint" {
  value = "https://api.${var.domain_name}"
}

output "api_gateway_id" {
  value = aws_apigatewayv2_api.main.id
}

output "lambda_function_name" {
  value = aws_lambda_function.api.function_name
}

output "lambda_function_arn" {
  value = aws_lambda_function.api.arn
}
