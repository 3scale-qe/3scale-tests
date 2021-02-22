<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
	version="1.0"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:param name="approver"/>
    <xsl:key name="issue-ids" match="//property[@name ='issue-id']" use="@value"/>

    <!-- https://source.redhat.com/groups/public/polarion/polarion_wiki/polarion_requirements_importer -->
    <!-- https://mojo.redhat.com/docs/DOC-1163149 -->
    <xsl:template match="/">
        <requirements project-id="{//property[@name = 'polarion-project-id']/@value}">
            <properties>
                <property name="lookup-method" value="name"/>
            </properties>
            <requirement severity-id="should_have" priority-id="high" approver-ids="{$approver}:approved" status-id="approved">
                <title>E2E Testing</title>
                <description>All the (automation?) testing that doesn't fall elsewhere</description>
            <custom-fields>
                <custom-field id="reqtype" content="functional"/>
            </custom-fields>
            </requirement>
            <xsl:for-each select="//property[@name='issue-id' and generate-id() = generate-id(key('issue-ids', @value)[1])]">
                <requirement id="{@value}" severity-id="should_have" priority-id="high" approver-ids="{$approver}:approved" assignee-id="{$approver}" status-id="approved">
                    <title><xsl:value-of select="@value"/></title>
                    <description><xsl:value-of select="../property[@name = 'issue']/@value"/></description>
                    <custom-fields>
                        <custom-field id="reqtype" content="functional"/>
                    </custom-fields>
                </requirement>
            </xsl:for-each>
        </requirements>
    </xsl:template>
</xsl:stylesheet>
