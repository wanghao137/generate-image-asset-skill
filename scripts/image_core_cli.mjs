#!/usr/bin/env node
import {
  calculateImageSize,
  deriveInheritedTarget,
  parseImageSize,
  validateImageJobRequest,
  verifySourceFinalInvariant,
} from '../vendor/image-job-core/index.mjs'

const [command, raw = '{}'] = process.argv.slice(2)
const input = JSON.parse(raw)
let result
if (command === 'derive-target') result = deriveInheritedTarget(input.source, input.options)
else if (command === 'calculate-size') result = { size: calculateImageSize(input.tier, input.ratio) }
else if (command === 'parse-size') result = parseImageSize(input.size)
else if (command === 'validate-job') result = validateImageJobRequest(input)
else if (command === 'verify-invariant') result = verifySourceFinalInvariant(input.source, input.final)
else throw new Error(`unknown image core command: ${command}`)
process.stdout.write(`${JSON.stringify(result)}\n`)
