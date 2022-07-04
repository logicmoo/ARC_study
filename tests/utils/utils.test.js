const validator = require("validator");
const utils = require("../../src/utility/utils");

const _ = require('lodash');


it('expect a number', async () => {

  expect( utils.isNumber(-1) ).toEqual( true );
  expect( utils.isNumber(1) ).toEqual( true );
  expect( utils.isNumber(0) ).toEqual( true );
  expect( utils.isNumber('') ).toEqual( false );
  expect( utils.isNumber(' ') ).toEqual( false );
  expect( utils.isNumber('one') ).toEqual( false );
  expect( utils.isNumber([]) ).toEqual( false );
  expect( utils.isNumber({}) ).toEqual( false );

});


function isElementAString (el) { return Object.prototype.toString.call(el) === '[object String]';  };

function isElementADate (el) { return Object.prototype.toString.call(el) === '[object Date]'; };


it('Newing up date from string that is not a date returns a Date, but it is an Invalid Date', async () => {

  let badString = `Bad String `;
  let newDate;

  try{
    newDate = new Date(badString);
    // console.log(`1. console log thinks Bad String is: `, newDate);  // Invalid Date
    // console.log(`2. is it a date?: `, isElementADate(newDate));  // true
    expect( isElementADate(newDate) ).toEqual( true );

    // But, just because it's a date object does not mean it's a valid date;
    // console.log(`3. newDate.toString() === 'Invalid Date': `, newDate.toString() === 'Invalid Date');
    expect( newDate.toString() === 'Invalid Date' ).toEqual( true );

    // Can we convert the date into a string?  Yes, but it's 'Invalid Date'
    // console.log(`4. newDate.toString(): `, newDate.toString());   // Invalid Date
    expect( isElementAString(newDate.toString()) ).toEqual( true );

    //  Validator does not think the badString is an isISO8601
    // console.log(`5. validator.isISO8601 (badString): `, validator.isISO8601 (badString)); // false
    expect( validator.isISO8601 (badString) ).toEqual( false );

    // Can we convert the date into an isoString?  No, this throws an exception
    // console.log(`6. the date string is: `, newDate.toISOString()); // RangeError: Invalid time value
    expect( isElementAString(newDate.toISOString()) ).toEqual( true );

    // Are the strings equal?  Nope, different formats.
    // console.log(`7. newDate.toISOString() === newDate.toString()`, newDate.toISOString() === newDate.toString());
    expect( newDate.toISOString() === newDate.toString() ).toEqual( false );

  }

  catch (err) {
    // console.log(`sorry, that's not a date`, err);
  }

});


it('Newing up date with an empty string returns a Date, but it is an Invalid Date', async () => {

  let emptyString = ``;
  let newDate;

  try{
    newDate = new Date(emptyString);
    // console.log(`1. console log thinks the empty string is: `, newDate);  // Invalid Date
    // console.log(`2. is it a date?: `, isElementADate(newDate));  // true
    expect( isElementADate(newDate) ).toEqual( true );

    // But, just because it's a date object does not mean it's a valid date;
    // console.log(`3. newDate.toString() === 'Invalid Date': `, newDate.toString() === 'Invalid Date');
    expect( newDate.toString() === 'Invalid Date' ).toEqual( true );

    // Can we convert the date into a string?  Yes, but it's 'Invalid Date'
    // console.log(`4. newDate.toString(): `, newDate.toString());   // Invalid Date
    expect( isElementAString(newDate.toString()) ).toEqual( true );

    //  Validator does not think the emptyString is an isISO8601
    // console.log(`5. validator.isISO8601 (emptyString): `, validator.isISO8601 (emptyString)); // false
    expect( validator.isISO8601 (emptyString) ).toEqual( false );

    // Can we convert the date into an isoString?  No, this throws an exception
    // console.log(`6. the date string is: `, newDate.toISOString()); // RangeError: Invalid time value
    expect( isElementAString(newDate.toISOString()) ).toEqual( true );

    // Are the strings equal?  Nope, different formats.
    // console.log(`7. newDate.toISOString() === newDate.toString()`, newDate.toISOString() === newDate.toString());
    expect( newDate.toISOString() === newDate.toString() ).toEqual( false );

  }

  catch (err) {
    // console.log(`sorry, that's not a date`, err);
  }

});



it('Newing up date with an string with an empty object returns a Date, but it is an Invalid Date', async () => {

  let emptyObjectString = `{}`;
  let newDate;

  try{
    newDate = new Date(emptyObjectString);
    // console.log(`1. console log thinks the empty string is: `, newDate);  // Invalid Date
    // console.log(`2. is it a date?: `, isElementADate(newDate));  // true
    expect( isElementADate(newDate) ).toEqual( true );

    // But, just because it's a date object does not mean it's a valid date;
    // console.log(`3. newDate.toString() === 'Invalid Date': `, newDate.toString() === 'Invalid Date');
    expect( newDate.toString() === 'Invalid Date' ).toEqual( true );

    // Can we convert the date into a string?  Yes, but it's 'Invalid Date'
    // console.log(`4. newDate.toString(): `, newDate.toString());   // Invalid Date
    expect( isElementAString(newDate.toString()) ).toEqual( true );

    //  Validator does not think the emptyObjectString is an isISO8601
    // console.log(`5. validator.isISO8601 (emptyObjectString): `, validator.isISO8601 (emptyObjectString)); // false
    expect( validator.isISO8601 (emptyObjectString) ).toEqual( false );

    // Can we convert the date into an isoString?  No, this throws an exception
    // console.log(`6. the date string is: `, newDate.toISOString()); // RangeError: Invalid time value
    expect( isElementAString(newDate.toISOString()) ).toEqual( true );

    // Are the strings equal?  Nope, different formats.
    // console.log(`7. newDate.toISOString() === newDate.toString()`, newDate.toISOString() === newDate.toString());
    expect( newDate.toISOString() === newDate.toString() ).toEqual( false );

  }

  catch (err) {
    // console.log(`sorry, that's not a date`, err);
  }

});




it('Newing up a date from string with forward slashes returns a valid date', async () => {

  let whackDate = `1/1/2015`;
  let newDate;

  try{
    newDate = new Date(whackDate);
    // console.log(`1. the date is: `, newDate);  // 2015-01-01T05:00:00.000Z
    // console.log(`2. is it a date?: `, isElementADate(newDate));  // true
    expect( isElementADate(newDate) ).toEqual( true );

    // But, just because it's a date object does not mean it's a valid date; but this is.
    // console.log(`3. newDate.toString() !== 'Invalid Date': `, newDate.toString() !== 'Invalid Date');
    expect( newDate.toString() !== 'Invalid Date' ).toEqual( true );  // But it is a valid date

    // Can we convert the date into a string?
    // console.log(`4. newDate.toString(): `, newDate.toString());   // Thu Jan 01 2015 00:00:00 GMT-0500 (EST)
    expect( isElementAString(newDate.toString()) ).toEqual( true );

    // Can we convert the date into an isoString?
    // console.log(`5. the date string is: `, newDate.toISOString()); // 2015-01-01T05:00:00.000Z
    expect( isElementAString(newDate.toISOString()) ).toEqual( true );

    //  Validator does not think the whack date is an isISO8601
    // console.log(`6. validator.isISO8601 (whackDate): `, validator.isISO8601 (whackDate)); // false
    expect( validator.isISO8601 (whackDate) ).toEqual( false );

    // Are the strings equal?  Nope, different formats.
    // console.log(`7. newDate.toISOString() === newDate.toString()`, newDate.toISOString() === newDate.toString());
    expect( newDate.toISOString() === newDate.toString() ).toEqual( false );

  }

  catch (err) {
    // console.log(`sorry, that's not a date`, err);
  }

});




it('Newing up a date from string with dashes returns a valid date', async () => {

  let dashDate = `1-1-2015`;
  let newDate;

  try{
    newDate = new Date(dashDate);
    // console.log(`1. the date is: `, newDate);  // 2015-01-01T05:00:00.000Z
    // console.log(`2. is it a date?: `, isElementADate(newDate));  // true
    expect( isElementADate(newDate) ).toEqual( true );

    // But, just because it's a date object does not mean it's a valid date; but this is.
    // console.log(`3. newDate.toString() !== 'Invalid Date': `, newDate.toString() !== 'Invalid Date');
    expect( newDate.toString() !== 'Invalid Date' ).toEqual( true );  // But it is a valid date

    // Can we convert the date into a string?
    // console.log(`4. newDate.toString(): `, newDate.toString());   // Thu Jan 01 2015 00:00:00 GMT-0500 (EST)
    expect( isElementAString(newDate.toString()) ).toEqual( true );

    // Can we convert the date into an isoString?
    // console.log(`5. the date string is: `, newDate.toISOString()); // 2015-01-01T05:00:00.000Z
    expect( isElementAString(newDate.toISOString()) ).toEqual( true );

    //  Validator does not think the dash date is an isISO8601
    // console.log(`6. validator.isISO8601 (dashDate): `, validator.isISO8601 (dashDate)); // false
    expect( validator.isISO8601 (dashDate) ).toEqual( false );

    // Are the strings equal?  Nope, different formats.
    // console.log(`7. newDate.toISOString() === newDate.toString()`, newDate.toISOString() === newDate.toString());
    expect( newDate.toISOString() === newDate.toString() ).toEqual( false );

  }

  catch (err) {
    // console.log(`sorry, that's not a date`, err);
  }

});



it('Newing up a date from a Date.toString() returns a valid date', async () => {

  let toStringDate = `Thu Jan 01 2015 00:00:00 GMT-0500 (EST)`;
  let newDate;

  try{
    newDate = new Date(toStringDate);
    // console.log(`1. console log things the date Thu Jan 01 2015 00:00:00 GMT-0500 (EST) is: `, newDate);  // 2015-01-01T05:00:00.000Z
    // console.log(`2. is it a date?: `, isElementADate(newDate));  // true
    expect( isElementADate(newDate) ).toEqual( true );

    // But, just because it's a date object does not mean it's a valid date; but this is.
    // console.log(`3. newDate.toString() !== 'Invalid Date': `, newDate.toString() !== 'Invalid Date');
    expect( newDate.toString() !== 'Invalid Date' ).toEqual( true );  // But it is a valid date

    // Can we convert the date into a string?
    // console.log(`4. newDate.toString(): `, newDate.toString());   // Thu Jan 01 2015 00:00:00 GMT-0500 (EST)
    expect( isElementAString(newDate.toString()) ).toEqual( true );

    // Can we convert the date into an isoString?
    // console.log(`5. the date string is: `, newDate.toISOString()); // 2015-01-01T05:00:00.000Z
    expect( isElementAString(newDate.toISOString()) ).toEqual( true );

    //  Validator does not think the whack date is an isISO8601
    // console.log(`6. validator.isISO8601 (toStringDate): `, validator.isISO8601 (toStringDate)); // false
    expect( validator.isISO8601 (toStringDate) ).toEqual( false );

    // Are the strings equal?  Nope, different formats.
    // console.log(`7. newDate.toISOString() === newDate.toString()`, newDate.toISOString() === newDate.toString());
    expect( newDate.toISOString() === newDate.toString() ).toEqual( false );

  }

  catch (err) {
    // console.log(`sorry, that's not a date`, err);
  }

});




it('Newing up a date from a number that is date-like returns a valid date', async () => {

  let dateLikeNumber = `01012015`;
  let newDate;

  try{
    newDate = new Date(dateLikeNumber);
    // console.log(`1. console log thinks the number 01012015: `, newDate);  // Invalid Date
    // console.log(`2. is it a date?: `, isElementADate(newDate));  // true
    expect( isElementADate(newDate) ).toEqual( true );

    // But, just because it's a date object does not mean it's a valid date;
    // console.log(`3. newDate.toString() === 'Invalid Date': `, newDate.toString() === 'Invalid Date');
    expect( newDate.toString() === 'Invalid Date' ).toEqual( true );

    // Can we convert the date into a string?  Yes, but it's 'Invalid Date'
    // console.log(`4. newDate.toString(): `, newDate.toString());   // Invalid Date
    expect( isElementAString(newDate.toString()) ).toEqual( true );

    //  Validator does not think the dateLikeNumber is an isISO8601
    // console.log(`5. validator.isISO8601 (dateLikeNumber): `, validator.isISO8601 (dateLikeNumber)); // false
    expect( validator.isISO8601 (dateLikeNumber) ).toEqual( false );

    // Can we convert the date into an isoString?  No, this throws an exception
    // console.log(`6. the date string is: `, newDate.toISOString()); // RangeError: Invalid time value
    expect( isElementAString(newDate.toISOString()) ).toEqual( true );

    // Are the strings equal?  Nope, different formats.
    // console.log(`7. newDate.toISOString() === newDate.toString()`, newDate.toISOString() === newDate.toString());
    expect( newDate.toISOString() === newDate.toString() ).toEqual( false );

  }

  catch (err) {
    // console.log(`sorry, that's not a date`, err);
  }

});



it('Newing up a date from a number 1548987953798 returns a valid date', async () => {

  let dateLikeNumber = 1548987953798;
  let newDate;

  try{
    newDate = new Date(dateLikeNumber);
    // console.log(`1. console log thinks the number 01012015: `, newDate);  // Invalid Date
    // console.log(`2. is it a date?: `, isElementADate(newDate));  // true
    expect( isElementADate(newDate) ).toEqual( true );

    // But, just because it's a date object does not mean it's a valid date; but this is.
    // console.log(`3. newDate.toString() === 'Invalid Date': `, newDate.toString() === 'Invalid Date');
    expect( newDate.toString() === 'Invalid Date' ).toEqual( false );  // But it is a valid date

    // Can we convert the date into a string?  Yes.
    // console.log(`4. newDate.toString(): `, newDate.toString());  // Thu Jan 31 2019 21:25:53 GMT-0500 (EST)
    expect( isElementAString(newDate.toString()) ).toEqual( true );

    // Can we convert the date into an isoString?  Yes
    // console.log(`5. the date string is: `, newDate.toISOString()); // 2019-02-01T02:25:53.798Z
    expect( isElementAString(newDate.toISOString()) ).toEqual( true );

    // Are the strings equal?  Nope, different formats.
    // console.log(`6. newDate.toISOString() === newDate.toString()`, newDate.toISOString() === newDate.toString());
    expect( newDate.toISOString() === newDate.toString() ).toEqual( false );

    //  Does validator not think dateLikeNumber.toString() is an isISO8601 string;  Nope.
    // console.log(`7. validator.isISO8601 (dateLikeNumber.toString()): `,
    //  validator.isISO8601 (dateLikeNumber.toString())); // false
    expect( validator.isISO8601 (dateLikeNumber.toString() ) ).toEqual( false );

  }

  catch (err) {
    // console.log(`sorry, that's not a date`, err);
  }

});




it('object should have exactly the given array of properties', async () => {
  let o = { prop1: 1, prop2: 2, prop3: 3 };
  let p = ['prop1', 'prop2', 'prop3'];
  expect( utils.hasAllAndOnlyTheseProperties(o, p) ).toEqual( true );
});

it('object does not have exactly the given array of properties (too many)', async () => {
  let o = { prop1: 1, prop2: 2, prop3: 3, prop4: 4 };
  let p = ['prop1', 'prop2', 'prop3'];
  expect( utils.hasAllAndOnlyTheseProperties(o, p) ).toEqual( false );
});

it('object does not have exactly the given array of properties (too few)', async () => {
  let o = { prop1: 1, prop2: 2 };
  let p = ['prop1', 'prop2', 'prop3'];
  expect( utils.hasAllAndOnlyTheseProperties(o, p) ).toEqual( false );
});

it('it is true that an object with no properties has exactly no properties', async () => {
  let o = { };
  let p = [];
  expect( utils.hasAllAndOnlyTheseProperties(o, p) ).toEqual( true );
});

it('empty object should not have all of the given array of properties', async () => {
  let o = { };
  let p = ['prop1', 'prop2', 'prop3'];
  expect( utils.hasAtLeastTheseProperties(o, p) ).toEqual( false );
});

it('object should have all of the given array of properties', async () => {
  let o = { prop1: 1, prop2: 2, prop3: 3 };
  let p = ['prop1', 'prop2', 'prop3'];
  expect( utils.hasAtLeastTheseProperties(o, p) ).toEqual( true );
});

it('object has all of the given array of properties', async () => {
  let o = { prop1: 1, prop2: 2, prop3: 3, prop4: 4 };
  let p = ['prop1', 'prop2', 'prop3'];
  expect( utils.hasAtLeastTheseProperties(o, p) ).toEqual( true );
});

it('object does not have all of the given array of properties', async () => {
  let o = { prop1: 1, prop2: 2 };
  let p = ['prop1', 'prop2', 'prop3'];
  expect( utils.hasAtLeastTheseProperties(o, p) ).toEqual( false );
});

it('it is true that an object with no properties has all properties in an array of properties', async () => {
  let o = { };
  let p = [];
  expect( utils.hasAtLeastTheseProperties(o, p) ).toEqual( true );
});


it('it is true that an object with all and only properties in an array has only properties in the array', async () => {
  let o = { prop1: 1, prop2: 2, prop3: 3 };
  let p = ['prop1', 'prop2', 'prop3'];
  expect( utils.hasOnlyTheseProperties(o, p) ).toEqual( true );
});

it('it is false that an object with properties not in a given array of properties has only those properties', async () => {
  let o = { prop1: 1, prop2: 2, prop3: 3, prop4: 4 };
  let p = ['prop1', 'prop2', 'prop3'];
  expect( utils.hasOnlyTheseProperties(o, p) ).toEqual( false );
});

it('it is true that an object with some and only properties in a given array of properties has only those properties', async () => {
  let o = { prop1: 1, prop2: 2 };
  let p = ['prop1', 'prop2', 'prop3'];
  expect( utils.hasOnlyTheseProperties(o, p) ).toEqual( true );
});

it('it is true that an object with no properties has only properties in an array of properties', async () => {
  let o = { };
  let p = [];
  expect( utils.hasOnlyTheseProperties(o, p) ).toEqual( true );
});

it('object with all and only properties in an array has no missing properties', async () => {
  let o = { prop1: 1, prop2: 2, prop3: 3 };
  let p = ['prop1', 'prop2', 'prop3'];
  let emptySet = new Set();
  expect( utils.missingProperties(o, p) ).toEqual( emptySet );
});

it('object with no properties in an array is missing all properties', async () => {
  let o = {};
  let p = ['prop1', 'prop2', 'prop3'];
  let missingSet = new Set(['prop1', 'prop2', 'prop3']);
  expect( utils.missingProperties(o, p) ).toEqual( missingSet );
});

it('object with two properties in an array of 3 is missing 1 properties', async () => {
  let o = { prop1: 1, prop2: 2, prop4: 4 };
  let p = ['prop1', 'prop2', 'prop3'];
  let missingSet = new Set(['prop3']);
  expect( utils.missingProperties(o, p) ).toEqual( missingSet );
});


// excess properties
it('it is true that an object with no properties has no excess properties in an array of properties', async () => {
  let o = { };
  let p = [];
  let emptySet = new Set();
  expect( utils.excessProperties(o, p) ).toEqual( emptySet );
});

it('object with all and only properties in an array has no excess properties', async () => {
  let o = { prop1: 1, prop2: 2, prop3: 3 };
  let p = ['prop1', 'prop2', 'prop3'];
  let emptySet = new Set();
  expect( utils.excessProperties(o, p) ).toEqual( emptySet );
});

it('object with no properties in an array has no excess properties', async () => {
  let o = {};
  let p = ['prop1', 'prop2', 'prop3'];
  let excessSet = new Set();
  expect( utils.excessProperties(o, p) ).toEqual( excessSet );
});

it('object with one property no in an array of 3 has an excess 1 properties', async () => {
  let o = { prop1: 1, prop2: 2, prop4: 4 };
  let p = ['prop1', 'prop2', 'prop3'];
  let excessSet = new Set(['prop4']);
  expect( utils.excessProperties(o, p) ).toEqual( excessSet );
});

// has excess properties
it('an object with no properties has no excess properties in an array of properties', async () => {
  let o = { };
  let p = [];
  expect( utils.hasExcessProperties(o, p) ).toEqual( false );
});

it('an object with one property in an array has no excess properties', async () => {
  let o = { prop1: 1 };
  let p = ['prop1', 'prop2', 'prop3'];
  expect( utils.hasExcessProperties(o, p) ).toEqual( false );
});

it('an object with one property excess properties over an empty array', async () => {
  let o = { prop1: 1 };
  let p = [];
  expect( utils.hasExcessProperties(o, p) ).toEqual( true );
});

it('an object with all and only properties in an array has no excess properties', async () => {
  let o = { prop1: 1, prop2: 2, prop3: 3 };
  let p = ['prop1', 'prop2', 'prop3'];
  expect( utils.hasExcessProperties(o, p) ).toEqual( false );
});

it('an object with no properties in an array has no excess properties', async () => {
  let o = {};
  let p = ['prop1', 'prop2', 'prop3'];
  expect( utils.hasExcessProperties(o, p) ).toEqual( false );
});

it('an object with two propertis not in an array of 3 has excess properties', async () => {
  let o = { prop1: 1, prop2: 2, prop4: 4 };
  let p = ['prop1', 'prop3', 'prop5'];
  expect( utils.hasExcessProperties(o, p) ).toEqual( true );
});

it('two objects with no properties are missing no properties an array of none', async () => {
  let o1 = {  };
  let o2 = {  };
  let p = [];
  let missing = new Set(p);
  expect( utils.missingPropertiesBetween(p, o1, o2) ).toEqual( missing );
});

it('two objects with no properties are missing 4 properties an array of 4', async () => {
  let o1 = {  };
  let o2 = {  };
  let p = ['prop1', 'prop2', 'prop3', 'prop4'];
  let missing = new Set(p);
  expect( utils.missingPropertiesBetween(p, o1, o2) ).toEqual( missing );
});

it('two objects with two properties with one in common are missing a property in an array of 4 properties', async () => {
  let o1 = { prop1: 1, prop2: 2,  };
  let o2 = { prop2: 1, prop3: 2 };
  let p = ['prop1', 'prop2', 'prop3', 'prop4'];
  let missing = new Set(['prop4']);
  expect( utils.missingPropertiesBetween(p, o1, o2) ).toEqual( missing );
});

it('two objects with two properties with one in common are not missing any properties in an empty array', async () => {
  let o1 = { prop1: 1, prop2: 2,  };
  let o2 = { prop2: 1, prop3: 2 };
  let p = [];
  let missing = new Set(p);
  expect( utils.missingPropertiesBetween(p, o1, o2) ).toEqual( missing );
});

it('An empty object and object with two properties are missing a property in an array of 4 properties', async () => {
  let o1 = {  };
  let o2 = { prop2: 1, prop3: 2 };
  let p = ['prop1', 'prop2', 'prop3', 'prop4'];
  let missing = new Set(['prop1', 'prop4']);
  expect( utils.missingPropertiesBetween(p, o1, o2) ).toEqual( missing );
});

it('an object with one property not in an array of 3 has excess properties', async () => {
  let o = { prop1: 1, prop2: 2, prop4: 4 };
  let p = ['prop1', 'prop2', 'prop3'];
  expect( utils.hasExcessProperties(o, p) ).toEqual( true );
});

//Some
it('it is false that an object with no properties has some properties in an array of no properties', async () => {
  let o = { };
  let p = [];
  expect( utils.hasSomeOfTheseProperties(o, p) ).toEqual( false );
});

it('it is false that an object with no properties has some properties in an array of one property', async () => {
  let o = { };
  let p = ['prop1'];
  expect( utils.hasSomeOfTheseProperties(o, p) ).toEqual( false );
});

it('it is true that an object with one property prop1 has some properties in an array of one property prop1', async () => {
  let o = { prop1: '' };
  let p = ['prop1'];
  expect( utils.hasSomeOfTheseProperties(o, p) ).toEqual( true );
});

it('it is true that an object with one property prop1 has some properties in an array of properties including prop1', async () => {
  let o = { prop1: '' };
  let p = ['prop1', 'prop2'];
  expect( utils.hasSomeOfTheseProperties(o, p) ).toEqual( true );
});

it('it is false that an object with one property prop1 has some properties in an array of properties not including prop1', async () => {
  let o = { prop1: '' };
  let p = ['prop3', 'prop2'];
  expect( utils.hasSomeOfTheseProperties(o, p) ).toEqual( false );
});

it('it is true that an object with properties including prop1 has some properties in an array of properties including prop1', async () => {
  let o = { prop1: '', prop2: 2 };
  let p = ['prop1' ];
  expect( utils.hasSomeOfTheseProperties(o, p) ).toEqual( true );
});

it('it is false that an object with several properties has some properties in an array of properties having no properties', async () => {
  let o = { prop1: '', prop2: 2 };
  let p = [ ];
  expect( utils.hasSomeOfTheseProperties(o, p) ).toEqual( false );
});


it('an object with a property whose value is an empty array is missing that property', async () => {
  let o = { uploads: [] };
  let p = [ 'uploads' ];

  let missing = utils.missingValuesInclusive(o, p);
  expect( [...missing] ).toEqual( p );
});


it('an object with a property whose value is an array with a value is not missing that property', async () => {
  let o = { uploads: [ 'a value' ] };
  let p = [ 'uploads' ];

  let missing = utils.missingValuesInclusive(o, p);
  expect( [...missing] ).toEqual( [] );
});


it('an object is missing fields if it does not have them or if it has them but they are empty', async () => {

  let o =  {
    "second_to_die_policy":"hdumbell5@gnu.org",
    "face_gt_100k":"true",
    "rated_above_a_minus":"true",
    "insured_us_citizen":"true",
    "medical_conditions":"minor_conditions",
    "cash_surrender_value":"sv_20_30",
    "outstanding_loans":"ol_20_30",
    "current_premiums_to_maturity":"cpm_3_4"
  };

  let p = [
    'case_nickname',
    'second_to_die_policy',
    'face_gt_100k',
    'rated_above_a_minus',
    'insured_us_citizen',
    'client_age_and_sex',
    'medical_conditions',
    'prequal_policy_type',
    'cash_surrender_value',
    'outstanding_loans',
    'current_premiums_to_maturity',
    'policy_premium_financed'
  ];

  let missing = utils.missingValuesInclusive(o, p);
  expect( [...missing] ).toEqual( ['case_nickname','client_age_and_sex','prequal_policy_type','policy_premium_financed'] );
});


it('split com ', async () => {
  let fqdn = 'com';
  expect(utils.splitOnLastDot(fqdn)).toEqual([ 'com' ]);
});
it('split one.com ', async () => {
  let fqdn = 'one.com';
  expect(utils.splitOnLastDot(fqdn)).toEqual([ 'one', 'com' ]);
});
it('split one.two.com ', async () => {
  let fqdn = 'one.two.com';
  expect(utils.splitOnLastDot(fqdn)).toEqual([ 'one.two', 'com' ]);
});
it('split one.two.three.com ', async () => {
  let fqdn = 'one.two.three.com';
  expect(utils.splitOnLastDot(fqdn)).toEqual([ 'one.two.three', 'com' ]);
});
it('split empty ', async () => {
  let fqdn = '';
  expect(utils.splitOnLastDot(fqdn)).toEqual([ '']);
});
it('split . ', async () => {
  let fqdn = '.';
  expect(utils.splitOnLastDot(fqdn)).toEqual(['', '']);
});
it('split .com. ', async () => {
  let fqdn = '.com.';
  expect(utils.splitOnLastDot(fqdn)).toEqual(['.com', '']);
});


it('utils.splitOnFirstDot com ', async () => {
  let fqdn = 'com';
  expect(utils.splitOnFirstDot(fqdn)).toEqual([ 'com' ]);
});
it('utils.splitOnFirstDot one.com ', async () => {
  let fqdn = 'one.com';
  expect(utils.splitOnFirstDot(fqdn)).toEqual([ 'one', 'com' ]);
});
it('utils.splitOnFirstDot one.two.com ', async () => {
  let fqdn = 'one.two.com';
  expect(utils.splitOnFirstDot(fqdn)).toEqual(['one', 'two.com' ]);
});
it('utils.splitOnFirstDot one.two.three.com ', async () => {
  let fqdn = 'one.two.three.com';
  expect(utils.splitOnFirstDot(fqdn)).toEqual([ 'one', 'two.three.com' ]);
});
it('utils.splitOnFirstDot empty ', async () => {
  let fqdn = '';
  expect(utils.splitOnFirstDot(fqdn)).toEqual([ '']);
});
it('utils.splitOnFirstDot . ', async () => {
  let fqdn = '.';
  expect(utils.splitOnFirstDot(fqdn)).toEqual(['', '']);
});
it('utils.splitOnFirstDot .com. ', async () => {
  let fqdn = '.com.';
  expect(utils.splitOnFirstDot(fqdn)).toEqual(['', 'com.']);
});

