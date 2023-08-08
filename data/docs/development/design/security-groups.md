# Design Document: Security Groups

## Introduction

The goal of this design document is to outline the implementation of security groups. Security groups will contain a set of rules that specify allowed ports and protocols on the driver interface. This will be managed using nftables and initially support Linux devices only.

## Phased Implementation

### Phase I - Default Security Group for Organization

This phase intends to work out the end-to-end implementation of policy from the API down to each device. To avoid making it harder than necessary, the first phase will only allow a single security group per organization that is managed by the organization owner.

- The default security group for an organization will be applied to all devices on startup.
- A device can only have one policy group applied at any given time in phase I. This means each organization will have a security group. Only the organization owner can CRUD the security group for a given organization. All users in the organization will have read access to this security group.
- When a new set of rules are applied, clear the appropriate chain and re-apply the rules. This can be more elegantly managed but introduces a great deal of complexity when rules are overlapping and may not be installed in the tables because another rule superseded it. See the section [Rule Deconfliction](#rule-deconfliction).

### Phase II - User-owned Security Groups

This phase adds user-defined security groups. When a user has applied a security group to a device

- Users can create security groups for more granular policies per device. The user owns the security group. This would be similar to how an ec2 security group gets applied to a node would be the same here with a patch.
- A device can only have one policy group applied at any given time. This means that a device will either have a user-defined policy OR the default security group for the organization applied.
- Only the user that owns the policy should have CRUD access to it.
- All members of an organization should have read access to all policies applied to any device in the organization.

### Phase III - Support for Multiple Security Groups

Prior phases only allowed a single security group policy per device. This phase would extend it to allow multiple policies.

- A device has the default policy for the organization applied by default.
- Instead of a device having a single policy, it is now a list. Once one or more user-defined policies are applied, that list is instead of the default security group, not in addition to it.
- Additional user-defined policies can be applied to a device. Their access should be the same as in phase II.
- The resulting behavior is that the allowed traffic is the sum of all policies as if they were combined into one, so combining rules into the same chains as before should be sufficient.

### Future Enhancement Ideas

This section includes ideas for future enhancements that need further exploration to define and determine if and how we would like to add them.

#### Robust Admin Organization Policies

- Overarching admin policies can be overlaid on top or in lieu of individual user policies. Further exploration needs to happen here.
- Admin policy should be able to override user policies, meaning an organization admin may want to be able to restrict which type of traffic can be opened by a user. This is very different than the policy features from the previous phases.
- Once more detail is available on the types of policy we would like to allow here, it can be further defined.

#### Symbolic Names

It would be convenient to be able to refer to devices with symbolic names instead of only IP ranges. This could potentially based on labels or tags applied to devices, for example.

## Default Security Group and Rules

Inbound rules:
Ultimately, the default security group rules for inbound traffic by default drop all inbound traffic unless there is a match of traffic in an established state. This match is referring to traffic that is part of an existing connection initiated by the device. In Phase I all inbound traffic will be allowed until a user-friendly mechanism to install rules in the UI or CLI is complete.

Outbound rules:
The agent will add a deny rule at the end of the egress chain only when an explicit allow rule is provisioned by the user.

- The default for Phase I of security groups is to permit any traffic in both directions. There will be one nftables table named `nexodus` containing two chains `nexodus-inbound` and `nexodus-outbound`. While these chains could be completely empty by default, I would propose the inbound chain have some basic permit-any rules accompanied by a drop-all rule. This is primarily to give some burn in time on any potential issues along with getting accustomed to defining a default policy since the explicit allow will eventually become an implicit deny-by-default rule on inbound traffic only if we follow the ec2 style model. The egress table will allow all traffic by default with an implicit allow-all, meaning an accept chain with no rules. If the user defines a policy blocking some protocol, destination address or destination ports those allow rules would be added, followed by a drop rule.
- At this time, our security group rules have no order associated with them. This is possible since there are no denies. As a reference, you can compare EC2 rules to Azure rules for not allowing deny statements vs allowing deny statements. The order begins to matter when deny rules are in place. This adds complexity which for our use case does not add any clear value.
- Users can add ranges of a given field. For example both, IpRanges with a value of `100.100.0.100-100.100.0.120` is valid and a prefix such as `100.100.0.128/25` is also valid. Along with that, a single address such as `100.100.0.10`.
- The same applies to source port and destination ports, `PortFrom:8080` coupled with `PortTo:9000` would equate to a rule of `8080-9000` being permitted. `PortFrom:0 PortTo:0` will be read as `ip permit <protocol> any`. `PortFrom:443 PortTo:443` would be equivalent to `ip permit <protocol> 4434`.
- L3 `IpRanges` are applied based on the direction field they are located in SecurityGroups. `InboundRules` have the IP prefix applied to the `saddr` field in nftables in the input chain, while `OutboundRules` are applied to the `daddr` field in the outbound chain.
- The layer 3 address is either the source address for inbound or the destination address for outbound rules.
- In regard to L4 ports, destination ports are what will be supported. For example, an ingress rule of `input tcp dport 22 counter accept` would apply port 22 to the L4 dport value in the `nexodus-inbound` chain meaning any host can connect to the node on port 22.
- The layer 4 port will always apply to the destination port regardless of whether it is in the inbound or outbound chain.
- There are some scenarios where data will need to be normalized. It also makes sense to pre-process rules for type checking and valid inputs before they arrive at the API server in locations such as `nexctl` and the UI, but there will likely need to be some rule validation in the security group handler. Here are some examples:
  - A user could specify protocol ip to ports 100-200. We would infer that would be TCP and UDP permit dport 100-200, performed in two rules.
  - Also, we may want to force ipv4 or ipv6 rather than allowing a generic ip value in Protocol. Alternatively, we can make an assumption that IP should imply both protocol families, v4 and v6. The same applies to ICMP, icmpv4 and icmpv6. Once we narrow in on the user experience via the web UI the appropriate path will likely be obvious.

Here is a functioning code example of the proposed default security rules with comments inline:

```go
    // default explicit permit ipv4 any rule
    explicitPermitIPv4Rule := models.SecurityRuleJson{
        IpProtocol: "ipv4", // Proto
        FromPort:   0,            // Starting Port Range
        ToPort:     0,            // Ending Port Range
        // IpRanges are any v4 or v6 addresses. Supported types are the same as nftables, such as:
        // 192.168.1.1, 192.168.1.0/24, 192.168.1.10-192.168.1.20, 
        // 2003:0db8:0000:0000:0000:0000:0000:0000-2003:0db8:ffff:ffff:ffff:ffff:ffff:ffff, 
        // 2001:0db8:1337:cafe::/64, fd00:face:b00c:cafe::4 etc.
        // Essentially, range x-y, cidr notation or individual addresses
        IpRanges:   []string{},
    }

    // default explicit permit ipv6 any rule
    explicitPermitIPv6Rule := models.SecurityRuleJson{
        IpProtocol: "ipv6",
        FromPort:   0,
        ToPort:     0,
        IpRanges:   []string{},
    }
    // default explicit permit icmp any rule
    explicitPermitIcmpIPv4Rule := models.SecurityRuleJson{
        IpProtocol: "icmp",
        FromPort:   0,
        ToPort:     0,
        IpRanges:   []string{},
    }
    // default explicit permit icmpv6 any rule
    explicitPermitIcmpIPv6Rule := models.SecurityRuleJson{
        IpProtocol: "icmpv6",
        FromPort:   0,
        ToPort:     0,
        IpRanges:   []string{},
    }

    inboundRules := []models.SecurityRuleJson{explicitPermitIPv4Rule, explicitPermitIPv6Rule, explicitPermitIcmpIPv4Rule, explicitPermitIcmpIPv6Rule}
    var outboundRules []models.SecurityRuleJson

    inboundRulesJSON, err := json.Marshal(inboundRules)
    if err != nil {
        return models.SecurityGroup{}, fmt.Errorf("error marshalling inbound rules: %w", err)
    }

    outboundRulesJSON, err := json.Marshal(outboundRules)
    if err != nil {
        return models.SecurityGroup{}, fmt.Errorf("error marshalling outbound rules: %w", err)
    }
```

Example default nftables table from the code above with comments inline. All rules are applied only to the driver interface:

```plaintext
table inet nexodus { // nftables table name
    chain nexodus-inbound { // ingress chain name
        type filter hook input priority filter; policy accept; // ingress chain policy
        ct state established,related iifname "wg0" counter packets 59 bytes 11407 accept // established ct tracking
        icmpv6 type { echo-request, echo-reply } iifname "wg0" counter packets 2 bytes 112 accept // permit icmpv6
        icmp type { echo-reply, echo-request } iifname "wg0" counter packets 1 bytes 84 accept // permit icmpv4
        meta nfproto ipv4 iifname "wg0" counter packets 1 bytes 64 accept // permit ipv4
        meta nfproto ipv6 iifname "wg0" counter packets 2 bytes 168 accept // permit ipv6
        iifname "wg0" counter packets 0 bytes 0 drop // drop any other traffic
    }

    chain nexodus-outbound { // egress chain name
        type filter hook input priority filter; policy accept; // 
    }
}
```

## Security Group User Interface

- The user can add rules via the web UI, the `nexctl` tool, or the HTTP API. Ideally, the credentials used by the agent would not have write access to these policies. However, until we have device-specific auth tokens available, there is no way to prevent it. That is a security feature tracked in [issue #647](https://github.com/nexodus-io/nexodus/issues/647).
- Users can modify the rules installed by Nexodus on the device if they have administrative access to nftables. The Nexodus Agent must reconcile what is currently applied to nftables with what is intended. This means that manual changes to the `nexodus` table are subject to being overwritten by the Nexodus Agent.

## Rule Deconfliction

- The deconfliction of user-provided rules is managed by nft. Let's look at the following example where a user defines a permit `icmp6 any` and an `icmp6 2001:0db8:1337:cafe::/64`. The JSON would look as follows:

```json
  {
    "ip_protocol": "icmp",
    "from_port": 0,
    "to_port": 0,
    "ip_ranges": [
      "2001:0db8:1337:cafe::/64"
    ]
  },
  {
    "ip_protocol": "icmp",
    "from_port": 0,
    "to_port": 0
  }
```

The actual rule in nftables would only insert the LPM (Longest Prefix Match). The resulting chain would look as follows.

```plaintext
table inet nexodus {
    chain nexodus-inbound {
        type filter hook input priority filter; policy accept;
        iifname "wg0" ct state established,related counter packets 0 bytes 0 accept
    }

    chain nexodus-outbound {
        type filter hook output priority filter; policy accept;
    }
```

The same LPM rule optimizations also apply to IPv4 and IPv6.

## New Tables

A new table will be defined for SecurityGroups

### SecurityGroups

- ID
- Name
- Description (SecurityRules JSON)
- InboundRules (SecurityRules JSON)
- OutboundRules (Security)
- OrganizationID (ZeroOrOne)
- UserID (ZeroOrOne)

### SecurityRules

Security rules will not be a new database but rules either inbound or outbound stored in the SecurityGroup field as JSON.

- ID
- SecurityGroupID
- Protocol
- FromPort
- ToPort
- Destination Address
- Destination Port
- OrganizationID

## CRUD Actions with API for Security Groups

In this section, we will outline the CRUD actions that can be performed using the API for managing security groups.

### Create Security Group

To create a new security group for an organization or user, send a POST request to the following endpoint with the required data:

Endpoint:

```plaintext
POST /organizations/$org_id/security_groups
POST /user/$org_id/security_groups

```

Payload

```json
{
  "group_name": "Example Security Group",
  "group_description": "A sample security group for demonstration purposes",
  "inbound_rules": [
    {
      "ip_protocol": "tcp",
      "from_port": 22,
      "to_port": 22,
      "ip_ranges": ["172.16.100.0/24"]
    }
  ],
  "outbound_rules": []
}
```

### Read Security Group(s)

To get a list of security groups for an organization or user, send a GET request to the following endpoint:

```plaintext
GET /organizations/$org_id/security_groups
GET /user/$org_id/security_groups
```

To get detailed information about a specific security group for an organization or user, send a GET request to the following endpoint:

```plaintext
GET /organizations/$org_id/security_groups/$sg_id
GET /user/$org_id/security_groups/$sg_id
```

### Update Security Group

To update a security group for an organization or user, send a PATCH request to the following endpoint with the updated data:

Endpoint:

```plaintext
PATCH /organizations/$org_id/security_groups/$sg_id
PATCH /users/$org_id/security_groups/$sg_id
```

Payload:

```json
{
  "group_name": "Updated Security Group",
  "group_description": "An updated security group for demonstration purposes",
  "inbound_rules": [
    {
      "ip_protocol": "tcp",
      "from_port": 22,
      "to_port": 22,
      "ip_ranges": ["10.100.0.0/20"]
    },
    {
      "ip_protocol": "udp",
      "from_port": 53,
      "to_port": 53,
      "ip_ranges": ["0.0.0.0/0"]
    }
  ],
  "outbound_rules": []
}
```

### Delete Security Group

To delete a security group for an organization or user, send a DELETE request to the following endpoint:

```plaintext
DELETE /organizations/$org_id/security_groups/$sg_id
DELETE /users/$org_id/security_groups/$sg_id
```

## New and Modified Structs

### Security Group Model

- New model

```go
// SecurityGroup represents a security group containing security rules and a group owner
type SecurityGroup struct {
    Base
    GroupName        string    `json:"group_name"`
    GroupDescription string    `json:"group_description"`
    OrganizationId   uuid.UUID `json:"org_id"`
    InboundRules     string    `json:"inbound_rules,omitempty" gorm:"type:JSONB; serializer:json"`
    OutboundRules    string    `json:"outbound_rules,omitempty" gorm:"type:JSONB; serializer:json"`
}

// AddSecurityGroup is the information needed to add a new Security Group.
type AddSecurityGroup struct {
    GroupName        string    `json:"group_name" example:"group_name"`
    GroupDescription string    `json:"group_description" example:"group_description"`
    OrganizationId   uuid.UUID `json:"org_id"`
    InboundRules     string    `json:"inbound_rules,omitempty" gorm:"type:JSONB; serializer:json"`
    OutboundRules    string    `json:"outbound_rules,omitempty" gorm:"type:JSONB; serializer:json"`
}

// UpdateSecurityGroup is the information needed to update an existing Security Group.
type UpdateSecurityGroup struct {
    GroupName        string `json:"group_name,omitempty"`
    GroupDescription string `json:"group_description,omitempty"`
    InboundRules     string `json:"inbound_rules,omitempty" gorm:"type:JSONB; serializer:json"`
    OutboundRules    string `json:"outbound_rules,omitempty" gorm:"type:JSONB; serializer:json"`
}
```

### Security Rules Struct

- New Struct. Rather than making a new table for Rules, we are embedding security rules as JSON into security group columns, `inbound_rules` and `outbound_rules`.

```go
// SecurityRuleJson represents a security rule
type SecurityRuleJson struct {
    IpProtocol string   `json:"ip_protocol"`
    FromPort   int64    `json:"from_port"`
    ToPort     int64    `json:"to_port"`
    IpRanges   []string `json:"ip_ranges,omitempty"`
}
```

### Other Table Changes

- Device

```go
type ModelsDevice struct {
    ...
    SecurityGroups  []uuid.UUID  `json:"security_groups,omitempty"`
}
```

- Organization: Every organization will receive a Security Group on creation.

```go
type ModelsOrganization struct {
    ...
    SecurityGroups  []uuid.UUID  `json:"security_groups,omitempty"`
}
```

- User

```go
type ModelsUser struct {
    ...
    SecurityGroups  []uuid.UUID  `json:"security_groups,omitempty"`
}
```

## Alternatives Considered

- A primary alternative is how much control to expose to the user. Specifically, do you allow the user to have access to deny rules? The benefits are not obvious and as referenced in [Default Security Group and Rules](#default-security-group-and-rules).
- Iptables user-space application for managing netfilter is the predominant acl implementation today but is planned for deprecation across all major Linux distributions.
