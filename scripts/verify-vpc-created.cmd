@echo off
set AWS_ACCESS_KEY_ID=test
set AWS_SECRET_ACCESS_KEY=test

echo Verificando recursos creados en LocalStack...
echo.

echo VPCs:
aws --endpoint-url=http://localhost:4566 ec2 describe-vpcs --region us-east-1 --query "Vpcs[?CidrBlock=='10.0.0.0/16'].[VpcId,CidrBlock,Tags[?Key=='Name'].Value|[0]]" --output table
echo.

echo Subnets:
aws --endpoint-url=http://localhost:4566 ec2 describe-subnets --region us-east-1 --query "Subnets[?VpcId!='vpc-6661ee789e7675748'].[SubnetId,CidrBlock,AvailabilityZone,Tags[?Key=='Name'].Value|[0]]" --output table
echo.

echo Security Groups:
aws --endpoint-url=http://localhost:4566 ec2 describe-security-groups --region us-east-1 --query "SecurityGroups[?VpcId!='vpc-6661ee789e7675748'].[GroupId,GroupName,VpcId]" --output table
echo.

echo NAT Gateways:
aws --endpoint-url=http://localhost:4566 ec2 describe-nat-gateways --region us-east-1 --query "NatGateways[*].[NatGatewayId,State,SubnetId]" --output table
