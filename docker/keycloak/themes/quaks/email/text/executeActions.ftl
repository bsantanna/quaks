<#ftl output_format="plainText">
<#assign requiredActionsText><#if requiredActions??><#list requiredActions><#items as reqActionItem>${msg("requiredAction.${reqActionItem}")}<#sep>, </#items></#list><#else></#if></#assign>

<#if (user.firstName)!?has_content>Hello ${(user.firstName)!},<#else>Hello,</#if>

${msg("executeActionsBody", link, linkExpiration, realmName, requiredActionsText, linkExpirationFormatter(linkExpiration))}
