<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
	version="1.0"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <!-- https://source.redhat.com/groups/public/polarion/polarion_wiki/polarion_results_xunit_importer -->
    <!-- https://mojo.redhat.com/docs/DOC-1073077 -->

    <xsl:param name="rmfails"/>
    <xsl:param name="polarionProperties"/>

    <xsl:template match="node()|@*">
        <!-- this copies all objects that do not match other template -->
        <xsl:copy>
            <xsl:apply-templates select="node()|@*"/>
        </xsl:copy>
    </xsl:template>

    <xsl:template match="/testsuites">
        <xsl:copy>
            <xsl:if test="$polarionProperties">
                <xsl:copy-of select="./testsuite/properties"/>
            </xsl:if>
            <xsl:apply-templates select="node()|@*"/>
        </xsl:copy>
    </xsl:template>

    <xsl:template match="testcase[skipped]"/>
    <xsl:template match="testsuite/@skipped">
        <xsl:attribute name="skipped">0</xsl:attribute>
    </xsl:template>

    <xsl:template match="testcase[failure or error]">
        <xsl:if test="not($rmfails)">
            <xsl:copy>
                <xsl:apply-templates select="node()|@*"/>
            </xsl:copy>
        </xsl:if>
    </xsl:template>
</xsl:stylesheet>
