# Claude Configuration Directory

This directory contains Claude Code skills and configurations for the California Complaint Generator project.

## Contents

### Skills

#### complaint-generator.md
A Claude Code skill for converting demand letters into California complaints.

**Usage:**
```
/skill complaint-generator
```

Or in Claude Code, simply mention that you want help with complaint generation and Claude will use this skill to guide you through the process.

**What it does:**
- Guides you through running the complaint generator
- Helps prepare input files
- Assists with reviewing and customizing output
- Ensures proper California formatting
- Provides quality control checklists

### GPT System Prompt

#### GPT_SYSTEM_PROMPT.md
Complete system instructions for creating a Custom GPT (ChatGPT) version of the California Complaint Generator.

**Usage:**
1. Go to ChatGPT and create a new Custom GPT
2. Copy the system prompt from this file
3. Paste into the GPT configuration
4. Configure as described in the file

**What it includes:**
- Complete system instructions for GPT
- California legal formatting requirements
- Cause of action templates
- Quality control standards
- Ethical guidelines
- Example interactions

## Using the Complaint Generator Skill

### With Claude Code

When working with Claude Code, you can invoke the complaint generator skill by:

1. **Explicit invocation:**
   ```
   Please help me with the complaint generator
   ```

2. **Contextual activation:**
   Simply mention you want to convert a demand letter to a complaint, and Claude will activate the skill.

3. **During the process:**
   The skill will guide you through:
   - Checking dependencies
   - Running the Python program
   - Reviewing output
   - Customizing the complaint
   - Quality checks

### With Custom GPT

If you prefer to use ChatGPT:

1. Create a Custom GPT using the system prompt in `GPT_SYSTEM_PROMPT.md`
2. Upload your demand letter to the GPT
3. Follow the GPT's guidance to generate the complaint
4. The GPT will output formatted complaint text
5. Copy to a Word document and apply formatting

## Files Structure

```
.claude/
├── README.md                    # This file
├── GPT_SYSTEM_PROMPT.md        # Custom GPT system instructions
└── skills/
    └── complaint-generator.md   # Claude Code skill
```

## Integration with Main Program

Both the skill and GPT system prompt work in conjunction with:
- `demand_to_complaint.py` - Main Python program
- `requirements.txt` - Python dependencies
- `COMPLAINT_GENERATOR_README.md` - Program documentation

## Which Should I Use?

**Use the Claude Code Skill when:**
- Working in a development environment
- Need to run the Python program directly
- Want automated file handling
- Prefer command-line workflow
- Working on a local machine

**Use the Custom GPT when:**
- Working in a browser
- Don't have Python installed
- Want to copy/paste text directly
- Prefer conversational interface
- Working from any device

**Use the Python Program directly when:**
- Already familiar with the tool
- Processing multiple complaints
- Have established workflow
- Don't need interactive guidance

## Extending the Skills

You can create additional skills for related tasks:

**Potential future skills:**
- `demand-letter-writer.md` - Generate demand letters
- `discovery-drafter.md` - Draft discovery requests
- `motion-writer.md` - Draft motions and oppositions
- `settlement-calculator.md` - Calculate settlement values

To add a new skill:
1. Create a new `.md` file in `.claude/skills/`
2. Write the skill instructions
3. Commit to the repository
4. Invoke with the skill name

## Best Practices

### For Skills
- Keep instructions clear and step-by-step
- Include troubleshooting sections
- Provide quality control checklists
- Reference main documentation

### For GPT Prompts
- Be comprehensive in system instructions
- Include ethical guidelines
- Provide example interactions
- Set clear limitations

### For Users
- Always review generated output
- Verify all factual allegations
- Have attorney review before filing
- Check local court rules
- Maintain confidentiality

## Support

For issues with:
- **The skill:** Check skill file syntax and Claude Code compatibility
- **The GPT:** Verify system prompt completeness and GPT configuration
- **The program:** See `COMPLAINT_GENERATOR_README.md`

## Updates

When updating:
1. Modify the appropriate files in `.claude/`
2. Test the skill/GPT with example inputs
3. Update this README if structure changes
4. Commit changes to version control

## License

These configuration files are part of the California Complaint Generator project and are provided for legal document preparation assistance.

## Disclaimer

These tools assist with document formatting and drafting. They do not:
- Provide legal advice
- Replace attorney review
- Guarantee legal sufficiency
- Practice law

Always consult with a licensed attorney before filing any legal documents.
