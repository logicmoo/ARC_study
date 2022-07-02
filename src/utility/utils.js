const validator = require("validator");
const _ = require('lodash');
const fs = require('fs');

function isUndefinedOrNull (s) {
  return s === undefined | s === null;
}
exports.isUndefinedOrNull = isUndefinedOrNull;


function isUndefinedOrNullOrStringNull (s) {
  return s === undefined | s === null | s === 'null';
}
exports.isUndefinedOrNullOrStringNull = isUndefinedOrNullOrStringNull;

function isNumber (val){
  if ((undefined === val) || (null === val)) {
    return false;
  }
  if(Array.isArray(val)) {
    return false;
  }
  if (typeof val === 'number') {
    return true;
  }
  return !isNaN(parseInt(val));
}
exports.isNumber = isNumber;

function isNumberGreaterThanZero(val){
 return  !isUndefinedOrNull(val)  && isNumber(val) && val > 0;
}
exports.isNumberGreaterThanZero = isNumberGreaterThanZero;

function isElementTheRightType(el, elementTypeType) {
  return Object.prototype.toString.call(el).includes(elementTypeType);
}
exports.isElementTheRightType = isElementTheRightType;

function isElementAString (el){
  return Object.prototype.toString.call(el) === '[object String]';
}
exports.isElementAString = isElementAString;

function isElementANumber(el) {
  return Object.prototype.toString.call(el) === '[object Number]';
}
exports.isElementANumber = isElementANumber;

function isElementAnObject(el) {
  return Object.prototype.toString.call(el) === '[object Object]';
}
exports.isElementAnObject = isElementAnObject;

function isElementAnArray(el) {
  return Object.prototype.toString.call(el) === '[object Array]';
}
exports.isElementAnArray = isElementAnArray;
function isElementABoolean(el) {
  return Object.prototype.toString.call(el) === '[object Boolean]';
}
exports.isElementABoolean = isElementABoolean;

function isElementADate(el) {
  return Object.prototype.toString.call(el) === '[object Date]';
}
exports.isElementADate = isElementADate;


exports.hasAllFieldsBetweenRequestAndPmcase = function (fields, requestBody, pmcase) {

  if(isUndefinedOrNull(fields) || fields.length === 0 ) {
    return false;
  }

  let hasAllfields = true;
  fields.forEach(item => {
    if(!_.has(requestBody, item) || isUndefinedOrNull(requestBody[item])
      || (Array.isArray(requestBody[item]) && requestBody[item].length === 0 )  ) {

      if(isUndefinedOrNull(pmcase) || isUndefinedOrNull(pmcase[item])
        || (Array.isArray(pmcase[item]) && pmcase[item].length === 0 ) ) {
        // we may have already posted/put it, but not completed it
        console.log('missing field:', item);
        hasAllfields = false;
      }
    }
  });
  return hasAllfields;
};


exports.hasSomeOfTheseProperties = function(object, arrayOfProperties) {
  return arrayOfProperties.some(p => {
    try {
      return !isUndefinedOrNull(object[p]);
    } catch (err) {
      return false;
    }
  });
};

exports.hasAllAndOnlyTheseProperties = function(object, arrayOfProperties) {

  let propertySet = new Set(arrayOfProperties);
  let objectSet = new Set(Object.keys(object));

  return _.isEqual(propertySet, objectSet);
};

exports.missingPropertiesBetween = function(arrayOfProperties, object1, object2 ) {

  let propertySet = new Set(arrayOfProperties);

  let object1Set = new Set(Object.keys(object1));
  let object2Set = new Set(Object.keys(object2));

  let combinedSet = new Set([...object1Set, ...object2Set]);

  return new Set(
    [...propertySet].filter(property => !combinedSet.has(property))
  ) ;
};

exports.missingProperties = function(object, arrayOfProperties) {

  let propertySet = new Set(arrayOfProperties);
  let objectSet = new Set(Object.keys(object));

  return new Set(
    [...propertySet].filter(property => !objectSet.has(property))
  ) ;
};

function logMissingValuesInclusive(oName, o, pName, p ) {

  // if(log.utils_missing_values_log >= module.exports.log_brief_info) {
  //   console.log('utils missingValuesInclusive.', `\n    ${oName}: ${o}   \n${pName}: ${p}`);
  // }

}

// If the field is missing, we do not its values as missing
exports.missingValues = function(object, arrayOfProperties) {

  let propertySet = new Set(arrayOfProperties);
  let objectSet = new Set(Object.keys(object));

  return new Set(
    [...propertySet].filter(property => objectSet.has(property)
      && isUndefinedOrNull(object[property]))
  ) ;
};

//  Here we take the convention that if the field is missing, so are its values
exports.missingValuesInclusive = function(object, arrayOfProperties) {
  logMissingValuesInclusive('object', JSON.stringify(object), 'properties', arrayOfProperties );

  let psInOurObject = Object.keys(object);
  let psWeDoNotHave = arrayOfProperties.filter( p => !psInOurObject.includes(p) );
  logMissingValuesInclusive('psInOurObject', psInOurObject, 'psWeDoNotHave', psWeDoNotHave);

  let psWeHaveWithEmptyValues = psInOurObject.filter(p => isUndefinedOrNull(object[p]));
  let psWeHaveWithEmptyArrays = psInOurObject
    .filter(p => (Array.isArray(object[p]) && object[p].length === 0) );
  logMissingValuesInclusive('psWeHaveWithEmptyValues', psWeHaveWithEmptyValues, 'psWeHaveWithEmptyArrays', psWeHaveWithEmptyArrays);

  let psMissingValues = psWeDoNotHave.concat(psWeHaveWithEmptyValues).concat(psWeHaveWithEmptyArrays);
  return new Set([...psMissingValues] );
};

exports.excessProperties = function(object, arrayOfProperties) {

  let propertySet = new Set(arrayOfProperties);
  let objectSet = new Set(Object.keys(object));

  return new Set(
    [...objectSet].filter(property => !propertySet.has(property))
  ) ;
};

exports.hasExcessProperties = function(object, arrayOfProperties) {
  let excessProperties =  module.exports.excessProperties(object, arrayOfProperties);
  return excessProperties.size > 0;
};

exports.hasAtLeastTheseProperties = function(object, arrayOfProperties) {
  return arrayOfProperties.every(p => p in object);
};

exports.hasOnlyTheseProperties = function(object, arrayOfProperties) {
  return Object.keys(object).every(k => arrayOfProperties.includes(k));
};

exports.checkFileExists = function(filepath){
  return new Promise((resolve, reject) => {
    fs.access(filepath, fs.F_OK, error => {
      resolve(!error);
    });
  });
};

exports.getRequiredNumberField = function(field, requestBody, pmcase) {

  if(_.has(requestBody, field) && module.exports.isNumber(requestBody[field])) {
    return requestBody[field];
  } else if (_.has(pmcase, field) && module.exports.isNumber(pmcase[field] )) {
    return pmcase[field];
  }

  return null;
};


exports.handler = async function (req, res, next, fun) {
  let logging = log.formLog(log.utils_handler_log, 'utils', 'handler');

  if (_.has(req, '__user') && _.has(req.__user, 'email') && !isUndefinedOrNull(req.__user.email)) {
    log.brief([`req.__user =`, req.__user], logging, 'request__user');
  }

  return await fun(req, res, next)
    .then(function (result) {
      log.verbose([`result=`, result], logging, 'result');
      if (Array.isArray(result)) {
        if (result[0] === 'success') {
          if (result[1]) {

            if (req.method === 'GET') {  log.brief([`success`], logging);
              return res.status(200).send(result[1]);
            }

            log.brief([`${req.method} received.`,result[1]], logging);
            return res.status(200).send([`${req.method} received.`, result[1]]);
          }
          log.brief([`success, no result:  ${req.method} received.`], logging);
          return res.status(200).send({'success': `${req.method} received.`});
        }
        log.error([`error. ${result}`], logging);
        return res.status(400).send(result[1]);
      }

      log.error([`validation failure. ${result}`], logging);
      return res.status(400).send(result); // could be a validation error

    }).catch(function (err) {
      return res.status(400).send(log.error([`error. ${err}`], logging));
    });
};

exports.handlerWithStatus = async function (req, res, next, fun) {

  let logging = log.formLog(log.utils_handler_with_status_log, 'utils', 'handler_with_status');

  if (_.has(req, '__user') && _.has(req.__user, 'email') && !isUndefinedOrNull(req.__user.email)) {
    log.brief([`req.__user =`, req.__user], logging, 'request__user');
  }

  if (req.body !== undefined && req.body !== null) {
    return await fun(req, res, next)
      .then(function (result) {
        log.verbose([`result: =`, result], logging, 'result');

        if (Array.isArray(result) && result[0] === 'success' ) {
          if(result[1]) {
            if(req.method === 'GET') {
              return res.status(200).send(result[1]);
            }

            return res.status(200).send([`${req.method} received.`, result[1]]);
          }
          return res.status(200).send({ 'success': `${req.method} received.` } );
         //  return;
        } else if (Array.isArray(result) && result[0] === 'failed' ) {
          return res.status(result[1]).send(result[2]);
        } else {
          return res.status(400).send(result); // could be a validation error
        }
      }).catch(function (err) {
        log.error([`error: =`, err], logging);
        return res.status(400).send(err);
      });
  }
};

function sanityCheckParams(reqParams, field, fieldlength, reqlength) {
  if (reqParams[field] === undefined || reqParams[field] === null || reqParams[field] === '') {

    if(log.sanity_check_logging_level >= module.exports.log_errors) {
      console.log('validation error sanity check=', reqParams);
    }

    return `{"invalid parameter: ${field}"}`;
  }

  if (typeof reqParams[field] === 'string' && !validator.isLength(reqParams[field], 1, fieldlength)) {
    return `{"invalid parameter length: ${field} should have no more than ${fieldlength} characters."}`;
  }
  if (!validator.isLength(JSON.stringify(reqParams), 1, reqlength)) {
    return `{"invalid parameter request length: ${field} should have no more than ${reqlength} characters."}`;
  }
  return '';
}
exports.sanityCheckParams = sanityCheckParams;

exports.validateIdList = function (idList) {

    for(let i=0; i<idList.length;i++) {
      let err = validateId(idList[i]);
      if(err !== '') {
        return err;
      }
    }

    return '';
};

function validateId (id) {
  let idObjectToValidate = { id: id.toString() };
  let err = sanityCheckParams(idObjectToValidate, 'id', 10, 30);
  if (err !== '') { return err; }
  if (!validator.isNumeric(id.toString(), { min: 0, max: 1000000000 })) {
    return '{ "id must be a number between 0 and 1,000,000,000" }';
  }
  return '';
}
exports.validateId = validateId;


exports.validateEmailAddress = function (email) {
  if (validator.isEmpty(email)) {
    if(log.email_validation_logging_level >= module.exports.log_errors) {
      console.log('Email validation error: ', '{"empty email"}');
    }
    return '{"empty email"}';
  }
  if (!validator.isLength(email, 6, 128)) {
    if(log.email_validation_logging_level >= module.exports.log_errors) {
      console.log('Email validation error: ', '{"email must contain between 6 and 128 characters"}');
    }
    return '{"email must contain between 6 and 128 characters"}';
  }
  if (!validator.isEmail(email)) {
    if(log.email_validation_logging_level >= module.exports.log_errors) {
      console.log('Email validation error: ', `{"mal-formed email address: ${email}"}`);
    }
    return `{"mal-formed email address: ${email}"}`;
  }
  return '';
};

function isIdInBody(req) {
  return _.has(req, 'body') && _.has(req.body, 'id');
}
exports.isIdInBody = isIdInBody;

function isIdInParams(req) {
  return _.has(req, 'params') && _.has(req.params, 'id');
}
exports.isIdInParams = isIdInParams;


function isIdInQuery(req) {
  return _.has(req, 'query') && _.has(req.query, 'id');
}
exports.isIdInQuery = isIdInQuery;

function getValidIdFromRequest(req, logging) {

  log.verbose(['req.query=', req.query], logging, 'request_body');

  let id = null;
  if (isIdInBody(req)) {
    id = req.body.id;
  } else if (isIdInParams(req)) {
    id = req.params.id;
  } else if (isIdInQuery(req)) {
    id = req.query.id;
  } else {
    return {error: '{ "id must be a number between 0 and 1,000,000,000" }'};
  }

  let err = validateId(id);
  if (err !== '') {
    return {error: err};
  }

  return id;
}
exports.getValidIdFromRequest = getValidIdFromRequest;


function uniq_fast(a) {
  let seen = {};
  let out = [];
  let len = a.length;
  let j = 0;
  for(let i = 0; i < len; i++) {
    let item = a[i];
    if(seen[item] !== 1) {
      seen[item] = 1;
      out[j++] = item;
    }
  }
  return out;
}
exports.uniq_fast = uniq_fast;

exports.deDup = function (requiredFields, invalidFields) {
  //console.log('before de-duping: requiredFields =', requiredFields.length, requiredFields, 'invalidFields =', invalidFields.length, invalidFields);
  requiredFields = uniq_fast(requiredFields);
  invalidFields = uniq_fast(invalidFields);
  //console.log('after de-duping: requiredFields =', requiredFields.length, requiredFields, 'invalidFields =', invalidFields.length, invalidFields);
  return [requiredFields,  invalidFields];
};

 exports.splitOnLastDot = function(fqdn) {
  let sp = fqdn.split('.');
  if(sp.length === 1) return sp;

  let final = sp.pop();
  return [ sp.join('.'), final ];
};

exports.splitOnFirstDot = function(fqdn) {
  let sp = fqdn.split('.');
  if(sp.length === 1) return sp;

  let first = sp.shift();
  return [  first, sp.join('.') ];
};

function hasObjectItem(object, item) {
  if(_.has(object, item)) return true;
  try {
    let section = object[item];
    return !isUndefinedOrNull(section);
  } catch (err) {
    return false;
  }
}
exports.hasObjectItem = hasObjectItem;

function hasValidObjectItem(object, item) {
//  if(_.has(object, item)) return true;
  try {
    let section = object[item];
    return !isUndefinedOrNull(section);
  } catch (err) {
    return false;
  }
}
exports.hasValidObjectItem = hasValidObjectItem;

function isPopulatedObject(object) {
  return !isUndefinedOrNull(object)  && isElementAnObject(object) && Object.keys(object).length > 0;
}
exports.isPopulatedObject = isPopulatedObject;

function isPopulatedArray(array) {
  return !isUndefinedOrNull(array)  && isElementAnArray(array) && array.length > 0;
}
exports.isPopulatedArray = isPopulatedArray;

function isPopulatedString(string) {
  return !isUndefinedOrNull(string)  && isElementAString(string) && string.length > 0;
}
exports.isPopulatedString = isPopulatedString;


function hasPopulatedArray(object, arrayName){
  return  isPopulatedObject(object)  && isPopulatedString(arrayName)
              && hasObjectItem(object, arrayName) && !isUndefinedOrNull(object[arrayName])
                && object[arrayName].length > 0;
}
exports.hasPopulatedArray = hasPopulatedArray;

function hasPopulatedArrayVerbose(object, arrayName, logging){

  if(!isPopulatedObject(object) )  {
    log.verbose([`Unpopulated object`], logging);
    return false;
  }

  if(!isPopulatedString(arrayName) )  {
    log.verbose([`Unpopulated string`], logging);
    return false;
  }

  if(!hasObjectItem(object, arrayName) )  {
    log.verbose([`No array of that name in the object`], logging);
    return false;
  }

  if(isUndefinedOrNull(object[arrayName]) )  {
    log.verbose([`Null value in object[arrayName]`], logging);
    return false;
  }

  if( !(object[arrayName].length > 0) )  {
    log.verbose([`Array is zero length`], logging);
    return false;
  }

  return true;

}
exports.hasPopulatedArrayVerbose = hasPopulatedArrayVerbose;

// Mongoose returns objects with funky wrapping; this turns it into a javascript object
function deMongoose(object) {
  return JSON.parse(JSON.stringify(object));
}
exports.deMongoose = deMongoose;

//  This assumes the section exists and is valid
function getDemongoosedItem(object, item) {
  return deMongoose(object)[item];
}
exports.getDemongoosedItem = getDemongoosedItem;

