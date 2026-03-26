<#if user.firstName?has_content>Hello ${user.firstName},<#else>Hello,</#if>

Your Quaks account has been activated. To complete your setup, please create a password using the link below.

${link}

This link will expire within ${linkExpirationFormatter(linkExpiration)}.

If you were not expecting this message, you can safely ignore it.

--
Quaks | https://quaks.ai
