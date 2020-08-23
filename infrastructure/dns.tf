resource "aws_route53_record" "sub" {
  zone_id = data.terraform_remote_state.root.outputs.root_zone_id
  name    = var.sub_domain_name
  type    = "CNAME"
  ttl     = "5"

  records = ["https://grocky.github.io/resume"]
}
