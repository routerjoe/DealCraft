import { Tool } from '@modelcontextprotocol/sdk/types.js';
import {
  getOutlookBidBoardEmails,
  getOutlookEmailDetails,
  downloadOutlookAttachments,
  markOutlookEmailAsRead,
} from '../../outlook/index.js';
import { join } from 'path';
import { getAttachmentsDir } from '../../utils/env.js';

export const outlookTools: Tool[] = [
  {
    name: 'outlook_get_bid_board_emails',
    description: 'Retrieves emails from the Bid Board folder in Outlook',
    inputSchema: {
      type: 'object',
      properties: {
        limit: {
          type: 'number',
          description: 'Maximum number of emails to retrieve (default: 50)',
        },
        unread_only: {
          type: 'boolean',
          description: 'Only retrieve unread emails (default: false)',
        },
      },
    },
  },
  {
    name: 'outlook_get_email_details',
    description: 'Gets full details of a specific email including body and attachments',
    inputSchema: {
      type: 'object',
      properties: {
        email_id: {
          type: 'string',
          description: 'The Outlook email ID',
        },
      },
      required: ['email_id'],
    },
  },
  {
    name: 'outlook_download_attachments',
    description: 'Downloads all attachments from a specific email',
    inputSchema: {
      type: 'object',
      properties: {
        email_id: {
          type: 'string',
          description: 'The Outlook email ID',
        },
        output_dir: {
          type: 'string',
          description: 'Optional custom output directory for attachments',
        },
      },
      required: ['email_id'],
    },
  },
  {
    name: 'outlook_mark_as_read',
    description: 'Marks an email as read in Outlook',
    inputSchema: {
      type: 'object',
      properties: {
        email_id: {
          type: 'string',
          description: 'The Outlook email ID',
        },
      },
      required: ['email_id'],
    },
  },
];

export async function handleOutlookTool(name: string, args: any) {
  switch (name) {
    case 'outlook_get_bid_board_emails': {
      const emails = await getOutlookBidBoardEmails(
        args.limit || 50,
        args.unread_only || false
      );
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({ emails, count: emails.length }, null, 2),
          },
        ],
      };
    }

    case 'outlook_get_email_details': {
      const details = await getOutlookEmailDetails(args.email_id);
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(details, null, 2),
          },
        ],
      };
    }

    case 'outlook_download_attachments': {
      const attachments = await downloadOutlookAttachments(
        args.email_id,
        args.output_dir
      );
      const attachmentDir = args.output_dir || join(getAttachmentsDir(), args.email_id);
       
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              email_id: args.email_id,
              directory: attachmentDir,
              saved: attachments,
              count: attachments.length,
            }, null, 2),
          },
        ],
      };
    }

    case 'outlook_mark_as_read': {
      const success = await markOutlookEmailAsRead(args.email_id);
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              email_id: args.email_id,
              success,
              status: success ? 'marked as read' : 'not modified',
            }, null, 2),
          },
        ],
      };
    }

    default:
      throw new Error(`Unknown Outlook tool: ${name}`);
  }
}
