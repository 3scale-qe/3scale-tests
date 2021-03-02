<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
	version="1.0"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:param name="approver"/>

    <!-- https://source.redhat.com/groups/public/polarion/polarion_wiki/polarion_test_case_importer -->
    <!-- https://mojo.redhat.com/docs/DOC-1075945 -->
    <xsl:template match="/">
        <testcases project-id="{//property[@name = 'polarion-project-id']/@value}">
            <properties>
                <property name="lookup-method" value="name"/>
            </properties>
            <xsl:apply-templates select="node()|@*"/>
        </testcases>
    </xsl:template>

    <xsl:template match="testcase">
        <xsl:variable name="name" select="concat(@classname, '.', @name)"/>
        <testcase id="{$name}" approver-ids="{$approver}:approved" status-id="approved">
            <title><xsl:value-of select="$name"/></title>
            <description><xsl:value-of select="$name"/></description>
            <custom-fields>
                <custom-field id="caseautomation" content="automated"/>
                <custom-field id="testtype" content="functional"/>
                <custom-field id="subtype1" content="integration"/>
                <custom-field id="caselevel" content="integration"/>
                <custom-field id="caseimportance" content="high"/>
                <custom-field id="automation_script" content="https://gitlab.cee.redhat.com/3scale-qe/3scale-py-testsuite"/>
            </custom-fields>
            <linked-work-items>
                <linked-work-item lookup-method="name" role-id="verifies" workitem-id="E2E Testing"/>
                <xsl:apply-templates select="properties/property"/>
            </linked-work-items>
        </testcase>
    </xsl:template>

    <xsl:template match="property[@name = 'issue-id']">
        <linked-work-item lookup-method="name" role-id="verifies" workitem-id="{@value}"/>
    </xsl:template>
</xsl:stylesheet>
