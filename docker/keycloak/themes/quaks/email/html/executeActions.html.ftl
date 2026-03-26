<#import "template.html.ftl" as layout>
<@layout.emailLayout>
<tr>
  <td style="font-family: Arial, sans-serif; font-size: 14px; color: #333333; padding: 24px;">
    <p><#if user.firstName?has_content>Hello ${user.firstName},<#else>Hello,</#if></p>
    <p>Your Quaks account has been activated. To complete your setup, please create a password using the link below.</p>
    <p style="text-align: center; margin: 32px 0;">
      <a href="${link}"
         style="background-color: #1a73e8; color: #ffffff; padding: 12px 28px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block;">
        Set your password
      </a>
    </p>
    <p>This link will expire within ${linkExpirationFormatter(linkExpiration)}.</p>
    <p>If you were not expecting this message, you can safely ignore it.</p>
    <hr style="border: none; border-top: 1px solid #eeeeee; margin: 24px 0;" />
    <p style="font-size: 12px; color: #999999;">
      Quaks &mdash; <a href="https://quaks.ai" style="color: #999999;">quaks.ai</a>
    </p>
  </td>
</tr>
</@layout.emailLayout>
